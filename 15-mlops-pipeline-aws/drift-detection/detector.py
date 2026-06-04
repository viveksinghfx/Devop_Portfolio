"""
Drift Detector — runs as a Kubernetes CronJob every 6 hours.

1. Fetches production prediction logs from S3 (last 24h)
2. Loads training reference dataset from S3
3. Runs Evidently data drift + data quality reports
4. Publishes PSI and drift scores to Prometheus Pushgateway
5. Triggers Kubeflow retraining pipeline if drift exceeds threshold
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timedelta

import boto3
import pandas as pd
import requests
from evidently.metric_preset import DataDriftPreset, DataQualityPreset
from evidently.report import Report
from prometheus_client import CollectorRegistry, Gauge, push_to_gateway

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# Config from environment
S3_BUCKET = os.environ["S3_BUCKET"]
REFERENCE_KEY = os.environ.get("REFERENCE_DATASET_KEY", "datasets/reference/latest.parquet")
PREDICTIONS_PREFIX = os.environ.get("PREDICTIONS_PREFIX", "predictions/")
PUSHGATEWAY_URL = os.environ.get("PUSHGATEWAY_URL", "http://prometheus-pushgateway:9091")
KFP_ENDPOINT = os.environ.get("KFP_ENDPOINT", "http://ml-pipeline.kubeflow:8888")
DRIFT_THRESHOLD = float(os.environ.get("DRIFT_THRESHOLD", "0.2"))
PSI_THRESHOLD = float(os.environ.get("PSI_THRESHOLD", "0.25"))
MODEL_NAME = os.environ.get("MODEL_NAME", "fraud-detector")


def fetch_reference_data(s3: boto3.client) -> pd.DataFrame:
    logger.info("Fetching reference dataset from s3://%s/%s", S3_BUCKET, REFERENCE_KEY)
    obj = s3.get_object(Bucket=S3_BUCKET, Key=REFERENCE_KEY)
    return pd.read_parquet(obj["Body"])


def fetch_production_data(s3: boto3.client, hours: int = 24) -> pd.DataFrame:
    """Fetch recent prediction logs from S3."""
    cutoff = datetime.utcnow() - timedelta(hours=hours)
    paginator = s3.get_paginator("list_objects_v2")
    frames = []

    for page in paginator.paginate(Bucket=S3_BUCKET, Prefix=PREDICTIONS_PREFIX):
        for obj in page.get("Contents", []):
            if obj["LastModified"].replace(tzinfo=None) > cutoff:
                body = s3.get_object(Bucket=S3_BUCKET, Key=obj["Key"])["Body"]
                frames.append(pd.read_parquet(body))

    if not frames:
        raise RuntimeError("No production data found in the last %d hours" % hours)

    df = pd.concat(frames, ignore_index=True)
    logger.info("Fetched %d production records", len(df))
    return df


def run_evidently_report(reference: pd.DataFrame, current: pd.DataFrame) -> dict:
    report = Report(metrics=[DataDriftPreset(), DataQualityPreset()])
    report.run(reference_data=reference, current_data=current)
    result = report.as_dict()

    drift_score = result["metrics"][0]["result"]["dataset_drift"]
    share_drifted = result["metrics"][0]["result"]["share_of_drifted_columns"]
    return {
        "dataset_drift_detected": drift_score,
        "share_drifted_columns": share_drifted,
        "per_feature": result["metrics"][0]["result"]["drift_by_columns"],
    }


def push_metrics(drift_results: dict) -> None:
    registry = CollectorRegistry()
    g_drift = Gauge("data_drift_score", "Share of drifted columns", registry=registry)
    g_drift.set(drift_results["share_drifted_columns"])

    for feature, info in drift_results["per_feature"].items():
        g_psi = Gauge(
            f"feature_drift_{feature.replace('-', '_')}",
            f"Drift score for feature {feature}",
            registry=registry,
        )
        g_psi.set(info.get("drift_score", 0.0))

    push_to_gateway(PUSHGATEWAY_URL, job="drift-detector", registry=registry)
    logger.info("Metrics pushed to Prometheus Pushgateway")


def trigger_retraining() -> None:
    """Kick off a new Kubeflow pipeline run via the KFP API."""
    logger.info("Drift threshold exceeded — triggering retraining pipeline")
    endpoint = f"{KFP_ENDPOINT}/apis/v2beta1/runs"
    payload = {
        "display_name": f"auto-retrain-drift-{datetime.utcnow().strftime('%Y%m%d-%H%M')}",
        "pipeline_spec": {
            "pipeline_id": os.environ["KFP_PIPELINE_ID"],
        },
        "runtime_config": {
            "parameters": {
                "dataset_version": "latest",
                "experiment_name": "drift-triggered-retrain",
            }
        },
    }
    resp = requests.post(endpoint, json=payload, timeout=30)
    resp.raise_for_status()
    run_id = resp.json()["run_id"]
    logger.info("Kubeflow run triggered: %s", run_id)


def main() -> None:
    s3 = boto3.client("s3")

    reference = fetch_reference_data(s3)
    current = fetch_production_data(s3)

    drift_results = run_evidently_report(reference, current)

    logger.info(
        "Drift results — dataset_drift: %s, share_drifted: %.2f",
        drift_results["dataset_drift_detected"],
        drift_results["share_drifted_columns"],
    )

    push_metrics(drift_results)

    if (
        drift_results["dataset_drift_detected"]
        or drift_results["share_drifted_columns"] > DRIFT_THRESHOLD
    ):
        trigger_retraining()
    else:
        logger.info("No significant drift detected. No retraining needed.")


if __name__ == "__main__":
    main()
