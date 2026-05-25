"""
Custom CVPilot business metrics. Standard HTTP metrics come from the
Instrumentator mounted in main.py.
"""

from __future__ import annotations

from prometheus_client import Counter, Histogram

evaluations_total = Counter(
    "cvpilot_evaluations_total",
    "Evaluations completed, partitioned by backend and final status.",
    labelnames=("backend", "status"),
)
evaluation_duration_seconds = Histogram(
    "cvpilot_evaluation_duration_seconds",
    "End-to-end evaluation duration (Celery task wall-clock).",
    labelnames=("backend",),
    buckets=(1, 5, 10, 30, 60, 120, 240, 480),
)
applications_submitted_total = Counter(
    "cvpilot_applications_submitted_total",
    "Application submissions partitioned by gate result.",
    labelnames=("result",),
)
wallet_send_total = Counter(
    "cvpilot_wallet_send_total",
    "Outbound GEN transfers partitioned by status.",
    labelnames=("status",),
)
contract_probe_total = Counter(
    "cvpilot_contract_probe_total",
    "Health probes of the deployed CVPilot contract.",
    labelnames=("result",),
)
