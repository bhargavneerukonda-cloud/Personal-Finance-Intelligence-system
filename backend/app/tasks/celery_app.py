"""
Celery application and async task definitions.

Tasks:
  - sync_bank_transactions: Pull latest transactions from Plaid
  - compute_health_score: Recompute financial health score for a user
  - send_budget_alert: Email/push notification for budget threshold
  - run_anomaly_scan: Scan new transactions for anomalies
  - embed_transactions: Upsert transaction embeddings to Pinecone
"""
import os
from celery import Celery
from celery.schedules import crontab

# Initialize Celery app
celery_app = Celery(
    "finsight",
    broker=os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379/1"),
    backend=os.environ.get("CELERY_RESULT_BACKEND", "redis://localhost:6379/2"),
    include=["app.tasks.tasks"],
)

# Configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_soft_time_limit=300,   # 5 min soft limit
    task_time_limit=600,        # 10 min hard limit
    # Retry policy
    task_max_retries=3,
    task_default_retry_delay=60,
)

# Periodic tasks (beat schedule)
celery_app.conf.beat_schedule = {
    # Sync transactions every hour
    "sync-all-users-transactions": {
        "task": "app.tasks.tasks.sync_all_users_transactions",
        "schedule": crontab(minute=0),  # Every hour
    },
    # Recompute health scores daily at 6am
    "compute-health-scores-daily": {
        "task": "app.tasks.tasks.compute_all_health_scores",
        "schedule": crontab(hour=6, minute=0),
    },
    # Run anomaly scan every 4 hours
    "run-anomaly-scan": {
        "task": "app.tasks.tasks.run_anomaly_scan_all_users",
        "schedule": crontab(minute=0, hour="*/4"),
    },
}
