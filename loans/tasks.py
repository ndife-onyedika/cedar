import logging

from celery import shared_task
from django.db import IntegrityError, transaction
from django.utils import timezone

from loans.mixins import task_exec

logger = logging.getLogger(__name__)


@shared_task
def due_task():
    today = timezone.now()
    try:
        with transaction.atomic():
            task_exec(context="due", date=today)
    except IntegrityError as e:
        error = f"ERROR: Loan Reminder Task!\nERROR_DESC: {e}"
        logger.error(error, exc_info=1)
        return error
    return f"SUCCESS: Loan Reminder Task!"


@shared_task
def interest_task():
    today = timezone.now()
    try:
        with transaction.atomic():
            task_exec(context="interest", date=today)
    except IntegrityError as e:
        error = f"ERROR: Loan Interest Calculation!\nERROR_DESC: {e}"
        logger.error(error, exc_info=1)
        return error
    return f"SUCCESS: Loan Interest Calculation!"
