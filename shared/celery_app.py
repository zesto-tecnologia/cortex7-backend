"""
Celery application configuration.
"""

from celery import Celery
from shared.config.settings import settings

# Create Celery application
celery_app = Celery(
    "cortex",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

# Configure Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

# Auto-discover tasks from all services
celery_app.autodiscover_tasks([
    "services.ai",
    "services.documents",
    "services.financial",
    "services.hr",
    "services.legal",
    "services.procurement",
])

