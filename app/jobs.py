import logging
import time
from datetime import datetime, timedelta, timezone

import redis
from rq import Queue


logger = logging.getLogger(__name__)


def send_due_soon_notification(task_title: str) -> None:
    time.sleep(5)
    logger.warning("Reminder: Task '%s' is due soon!", task_title)


def should_queue_notification(due_date):
    if due_date is None:
        return False

    now = datetime.now(timezone.utc)
    horizon = now + timedelta(hours=24)

    return now < due_date <= horizon


def get_queue(redis_url: str) -> Queue:
    redis_conn = redis.from_url(redis_url)
    return Queue("default", connection=redis_conn)
