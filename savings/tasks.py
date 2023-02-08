from celery import shared_task
from django.db import IntegrityError, transaction
from django.utils import timezone
from django.utils.timezone import datetime, timedelta

from accounts.models import Member, User
from savings.mixins import calculate_interest_exec, calculate_yearEndBalance
from settings.models import BusinessYear

from .models import SavingsInterest


@shared_task
def daily_interest_calculation_task():
    today = timezone.now()
    admin = User.objects.get(is_superuser=True)
    members = Member.objects.filter(is_active=True)
    by = BusinessYear.objects.last()
    bys = datetime(today.year - 1, by.start_month, by.start_day)
    bye = datetime(today.year, by.end_month, by.end_day) + timedelta(days=1)

    try:
        with transaction.atomic():
            for member in members:
                savings_intr = SavingsInterest.objects.filter(
                    member=member, is_comp=True, disabled=False
                )
                if savings_intr.count() > 0:
                    for saving_intr in savings_intr:
                        calculate_interest_exec(
                            admin=admin, member=member, instance=saving_intr, date=today
                        )
                if today.date() == bye.date():
                    date_range = [bys.date(), bye.date()]
                    calculate_yearEndBalance(member, date_range)
    except IntegrityError as e:
        return f"ERROR: Savings Interest Calculation!\nERROR_DESC: {e}"
    else:
        return f"SUCCESS: Savings Interest Calculation!"
