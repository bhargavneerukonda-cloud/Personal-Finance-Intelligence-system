"""
Async Celery task implementations.
"""
import httpx
import logging
from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def sync_user_transactions(self, user_id: str):
    """
    Pull latest transactions from Plaid for a single user.
    Triggered: after Plaid webhook or on-demand.
    """
    try:
        logger.info(f"Syncing transactions for user {user_id}")
        # In production: call Plaid transactions/sync, upsert to DB
        # from app.services.plaid_service import PlaidService
        # PlaidService.sync_transactions(user_id)
        return {"status": "success", "user_id": user_id}
    except Exception as exc:
        logger.error(f"Transaction sync failed for user {user_id}: {exc}")
        raise self.retry(exc=exc)


@celery_app.task(bind=True, max_retries=3)
def compute_health_score(self, user_id: str):
    """
    Recompute and persist financial health score for a user.
    Triggered: daily, or after significant transaction activity.
    """
    try:
        logger.info(f"Computing health score for user {user_id}")
        # In production: pull user financials from DB, call ML service, persist
        # score = FinancialHealthScorer().compute(user_data)
        # db.add(FinancialHealthScore(user_id=user_id, **score.__dict__))
        return {"status": "success", "user_id": user_id}
    except Exception as exc:
        raise self.retry(exc=exc)


@celery_app.task(bind=True, max_retries=3)
def send_budget_alert(self, user_id: str, category: str, utilization_pct: float):
    """
    Send budget alert email/push notification.
    Triggered: when a budget category crosses alert threshold.
    """
    try:
        logger.info(f"Sending budget alert to user {user_id}: {category} at {utilization_pct:.0%}")
        # In production: use SendGrid to send email
        # from app.services.notification_service import NotificationService
        # NotificationService.send_budget_alert(user_id, category, utilization_pct)
        return {"status": "sent", "user_id": user_id, "category": category}
    except Exception as exc:
        raise self.retry(exc=exc)


@celery_app.task(bind=True, max_retries=2)
def categorize_transaction(self, transaction_id: str, amount: float,
                            description: str, merchant_name: str = ""):
    """
    Call ML service to categorize a transaction and update DB.
    Triggered: immediately after a new transaction is created.
    """
    try:
        from app.core.config import settings
        import asyncio

        async def _call_ml():
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(
                    f"{settings.ML_SERVICE_URL}/predict/category",
                    json={
                        "transaction_id": transaction_id,
                        "amount": amount,
                        "description": description,
                        "merchant_name": merchant_name,
                    }
                )
                return resp.json()

        result = asyncio.run(_call_ml())
        logger.info(f"Categorized transaction {transaction_id}: {result.get('category')} ({result.get('confidence'):.2f})")
        return result
    except Exception as exc:
        logger.error(f"Categorization failed for transaction {transaction_id}: {exc}")
        raise self.retry(exc=exc)


@celery_app.task(bind=True, max_retries=2)
def scan_transaction_anomaly(self, transaction_id: str, amount: float,
                              category: str, transaction_date: str,
                              merchant_name: str = "", user_id: str = ""):
    """
    Check a new transaction for anomalies.
    Triggered: after transaction creation/categorization.
    """
    try:
        from app.core.config import settings
        import asyncio

        async def _call_ml():
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(
                    f"{settings.ML_SERVICE_URL}/predict/anomaly",
                    json={
                        "transaction_id": transaction_id,
                        "amount": amount,
                        "category": category,
                        "transaction_date": transaction_date,
                        "merchant_name": merchant_name,
                        "user_id": user_id,
                    }
                )
                return resp.json()

        result = asyncio.run(_call_ml())
        if result.get("flagged"):
            logger.warning(f"Anomaly flagged for transaction {transaction_id}: {result}")
            # In production: persist AnomalyFlag to DB and send alert
        return result
    except Exception as exc:
        raise self.retry(exc=exc)


@celery_app.task
def sync_all_users_transactions():
    """Periodic task: sync transactions for all active users."""
    logger.info("Starting periodic transaction sync for all users")
    # In production: query all active users with connected Plaid accounts
    # and enqueue individual sync tasks
    return {"status": "scheduled"}


@celery_app.task
def compute_all_health_scores():
    """Periodic task: recompute health scores for all active users."""
    logger.info("Starting periodic health score computation")
    return {"status": "scheduled"}


@celery_app.task
def run_anomaly_scan_all_users():
    """Periodic task: run anomaly scan on recent transactions."""
    logger.info("Starting periodic anomaly scan")
    return {"status": "scheduled"}
