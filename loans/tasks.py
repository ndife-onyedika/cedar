from celery import shared_task
from django.db import IntegrityError, transaction
from django.utils import timezone

from loans.mixins import task_exec


@shared_task
def due_task():
    today = timezone.now()
    try:
        with transaction.atomic():
            task_exec(context="due", date=today)
    except IntegrityError as e:
        return f"ERROR: Loan Reminder Task!\nERROR_DESC: {e}"
    else:
        return f"SUCCESS: Loan Reminder Task!"


@shared_task
def interest_task():
    today = timezone.now()
    try:
        with transaction.atomic():
            task_exec(context="interest", date=today)
    except IntegrityError as e:
        return f"ERROR: Loan Interest Calculation!\nERROR_DESC: {e}"
    else:
        return f"SUCCESS: Loan Interest Calculation!"
