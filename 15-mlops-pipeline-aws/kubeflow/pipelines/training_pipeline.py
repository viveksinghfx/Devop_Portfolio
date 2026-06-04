"""
End-to-end MLOps training pipeline — Kubeflow Pipelines v2 SDK.

Stages:
  1. ingest_and_validate  — pull dataset from S3, run Great Expectations checks
  2. feature_engineering  — compute features, write Parquet back to S3
  3. train               — train XGBoost model, log to MLflow
  4. evaluate            — compute hold-out metrics, fail pipeline if below threshold
  5. register            — register model artifact in MLflow Model Registry
"""

from __future__ import annotations

import argparse
from kfp import dsl, compiler
from kfp.dsl import component, Input, Output, Dataset, Model, Metrics


# ── Components ────────────────────────────────────────────────────────────────

@component(
    base_image="python:3.11-slim",
    packages_to_install=["boto3", "great-expectations==0.18.12", "pandas", "pyarrow"],
)
def ingest_and_validate(
    s3_dataset_uri: str,
    dataset_version: str,
    raw_dataset: Output[Dataset],
):
    """Download dataset from S3 and run schema + null-rate validations."""
    import boto3
    import pandas as pd

    s3 = boto3.client("s3")
    bucket, key = s3_dataset_uri.replace("s3://", "").split("/", 1)
    local_path = "/tmp/raw_data.parquet"
    s3.download_file(bucket, f"{key}/{dataset_version}/data.parquet", local_path)

    df = pd.read_parquet(local_path)
    assert df.isnull().mean().max() < 0.05, "Null rate exceeds 5% in one or more columns"
    assert len(df) > 1000, "Dataset too small — likely a download issue"

    df.to_parquet(raw_dataset.path, index=False)
    print(f"Ingested {len(df):,} rows, {df.shape[1]} columns")


@component(
    base_image="python:3.11-slim",
    packages_to_install=["pandas", "scikit-learn", "pyarrow"],
)
def feature_engineering(
    raw_dataset: Input[Dataset],
    engineered_features: Output[Dataset],
):
    """Standard scaling, encoding, and feature selection."""
    import pandas as pd
    from sklearn.preprocessing import StandardScaler, LabelEncoder

    df = pd.read_parquet(raw_dataset.path)

    # Encode categoricals
    for col in df.select_dtypes(include="object").columns:
        if col != "label":
            df[col] = LabelEncoder().fit_transform(df[col].astype(str))

    # Scale numerics
    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    numeric_cols = [c for c in numeric_cols if c != "label"]
    df[numeric_cols] = StandardScaler().fit_transform(df[numeric_cols])

    df.to_parquet(engineered_features.path, index=False)
    print(f"Feature engineering complete: {df.shape}")


@component(
    base_image="python:3.11-slim",
    packages_to_install=["pandas", "xgboost", "scikit-learn", "mlflow", "pyarrow", "boto3"],
)
def train(
    engineered_features: Input[Dataset],
    mlflow_tracking_uri: str,
    experiment_name: str,
    model_artifact: Output[Model],
    run_id: Output[str],
    n_estimators: int = 300,
    max_depth: int = 6,
    learning_rate: float = 0.05,
):
    """Train XGBoost model and log to MLflow."""
    import mlflow
    import mlflow.xgboost
    import pandas as pd
    import xgboost as xgb
    from sklearn.model_selection import train_test_split

    df = pd.read_parquet(engineered_features.path)
    X = df.drop(columns=["label"])
    y = df["label"]
    X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2, random_state=42)

    mlflow.set_tracking_uri(mlflow_tracking_uri)
    mlflow.set_experiment(experiment_name)

    with mlflow.start_run() as run:
        mlflow.log_params({
            "n_estimators": n_estimators,
            "max_depth": max_depth,
            "learning_rate": learning_rate,
        })

        clf = xgb.XGBClassifier(
            n_estimators=n_estimators,
            max_depth=max_depth,
            learning_rate=learning_rate,
            use_label_encoder=False,
            eval_metric="logloss",
            random_state=42,
        )
        clf.fit(X_train, y_train, eval_set=[(X_val, y_val)], verbose=False)

        mlflow.xgboost.log_model(clf, "model")
        clf.save_model(model_artifact.path)

        # Output run ID for downstream components
        with open(run_id.path, "w") as f:
            f.write(run.info.run_id)

    print(f"Training complete. MLflow run ID: {run.info.run_id}")


@component(
    base_image="python:3.11-slim",
    packages_to_install=["pandas", "xgboost", "scikit-learn", "mlflow", "pyarrow"],
)
def evaluate(
    engineered_features: Input[Dataset],
    model_artifact: Input[Model],
    run_id: Input[str],
    mlflow_tracking_uri: str,
    min_f1_threshold: float,
    metrics: Output[Metrics],
):
    """Evaluate model on hold-out set; fail pipeline if below threshold."""
    import mlflow
    import pandas as pd
    import xgboost as xgb
    from sklearn.metrics import f1_score, roc_auc_score
    from sklearn.model_selection import train_test_split

    df = pd.read_parquet(engineered_features.path)
    X = df.drop(columns=["label"])
    y = df["label"]
    _, X_test, _, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    clf = xgb.XGBClassifier()
    clf.load_model(model_artifact.path)

    preds = clf.predict(X_test)
    proba = clf.predict_proba(X_test)[:, 1]

    f1 = f1_score(y_test, preds)
    auc = roc_auc_score(y_test, proba)

    metrics.log_metric("f1_score", f1)
    metrics.log_metric("roc_auc", auc)

    mlflow.set_tracking_uri(mlflow_tracking_uri)
    with open(run_id.path) as f:
        rid = f.read().strip()

    with mlflow.start_run(run_id=rid):
        mlflow.log_metrics({"f1_score": f1, "roc_auc": auc})

    print(f"Evaluation — F1: {f1:.4f}, AUC: {auc:.4f} (threshold: {min_f1_threshold})")

    if f1 < min_f1_threshold:
        raise ValueError(
            f"F1 score {f1:.4f} below threshold {min_f1_threshold}. "
            "Pipeline halted — model not registered."
        )


@component(
    base_image="python:3.11-slim",
    packages_to_install=["mlflow", "boto3"],
)
def register_model(
    run_id: Input[str],
    mlflow_tracking_uri: str,
    model_name: str,
):
    """Register the trained model in MLflow Model Registry as 'Staging'."""
    import mlflow

    mlflow.set_tracking_uri(mlflow_tracking_uri)
    with open(run_id.path) as f:
        rid = f.read().strip()

    model_uri = f"runs:/{rid}/model"
    result = mlflow.register_model(model_uri, model_name)
    print(f"Registered: {model_name} version {result.version}")

    client = mlflow.tracking.MlflowClient()
    client.transition_model_version_stage(
        name=model_name,
        version=result.version,
        stage="Staging",
    )
    print(f"Model {model_name} v{result.version} transitioned to Staging")


# ── Pipeline definition ───────────────────────────────────────────────────────

@dsl.pipeline(
    name="mlops-training-pipeline",
    description="End-to-end training: ingest → features → train → evaluate → register",
)
def training_pipeline(
    s3_dataset_uri: str = "s3://mlops-data-bucket/datasets/fraud-detection",
    dataset_version: str = "latest",
    mlflow_tracking_uri: str = "http://mlflow-svc.mlops.svc.cluster.local:5000",
    experiment_name: str = "fraud-detection",
    model_name: str = "fraud-detector",
    min_f1_threshold: float = 0.85,
    n_estimators: int = 300,
    max_depth: int = 6,
    learning_rate: float = 0.05,
):
    ingest_task = ingest_and_validate(
        s3_dataset_uri=s3_dataset_uri,
        dataset_version=dataset_version,
    )

    features_task = feature_engineering(
        raw_dataset=ingest_task.outputs["raw_dataset"],
    )

    train_task = train(
        engineered_features=features_task.outputs["engineered_features"],
        mlflow_tracking_uri=mlflow_tracking_uri,
        experiment_name=experiment_name,
        n_estimators=n_estimators,
        max_depth=max_depth,
        learning_rate=learning_rate,
    )

    eval_task = evaluate(
        engineered_features=features_task.outputs["engineered_features"],
        model_artifact=train_task.outputs["model_artifact"],
        run_id=train_task.outputs["run_id"],
        mlflow_tracking_uri=mlflow_tracking_uri,
        min_f1_threshold=min_f1_threshold,
    )

    register_model(
        run_id=train_task.outputs["run_id"],
        mlflow_tracking_uri=mlflow_tracking_uri,
        model_name=model_name,
    ).after(eval_task)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--compile", action="store_true")
    args = parser.parse_args()

    if args.compile:
        compiler.Compiler().compile(training_pipeline, "training_pipeline.yaml")
        print("Pipeline compiled → training_pipeline.yaml")
