from datetime import time

from django.db import IntegrityError, transaction
from django.utils.timezone import datetime, make_aware, now, timedelta
from notifications.signals import notify


def set_nok(modeladmin, request, queryset):
    from savings.models import SavingsInterestTotal

    from .models import NextOfKin

    for instance in queryset:
        try:
            with transaction.atomic():
                si = SavingsInterestTotal.objects.filter(member=instance)
                if len(si) > 0:
                    si = si[0]
                    si.save()
                # NextOfKin.objects.get_or_create(member=instance)
        except IntegrityError as e:
            raise Exception(f"ACCOUNTNEXTOFKINACTION: {e}")


def run_task(modeladmin, request, queryset):
    from accounts.models import Member, User
    from savings.mixins import (
        calculate_interest_exec,
        calculate_yearEndBalance,
        check_activity_exec,
        handle_withdrawal,
    )
    from savings.models import SavingsDebit, SavingsInterestTotal

    members = Member.objects.all()
    admin = User.objects.get(is_superuser=True)

    for instance in queryset:
        try:
            with transaction.atomic():
                for year in range(now().year, now().year + 1):
                    start_date = now().date() - timedelta(days=1)
                    end_date = now().date()
                    delta = end_date - start_date
                    for i in range(delta.days + 1):
                        current_date = start_date + timedelta(days=i)
                        timestamp = make_aware(
                            datetime.combine(current_date, time(3, 0))
                        )
                        print(f"Working Timestamp: {current_date}")

                        for member in members:
                            if current_date < end_date:
                                is_active = check_activity_exec(member, timestamp)
                                if is_active:
                                    savings = SavingsInterestTotal.objects.filter(
                                        is_comp=True,
                                        member=member,
                                        disabled=False,
                                        created_at__date__lte=current_date,
                                    ).order_by("created_at")

                                    if savings.count() > 0:
                                        for saving in savings:
                                            calculate_interest_exec(
                                                admin=admin,
                                                member=member,
                                                date=timestamp,
                                                instance=saving,
                                            )

                                withdrawals = SavingsDebit.objects.filter(
                                    member=member,
                                    created_at__date=current_date,
                                ).order_by("created_at")
                                if withdrawals.count() > 0:
                                    for withdrawal in withdrawals:
                                        handle_withdrawal(
                                            context="create", instance=withdrawal
                                        )

                            if current_date == end_date:
                                date_range = [start_date, end_date]
                                calculate_yearEndBalance(member, date_range)

                        if (
                            current_date == end_date
                            and current_date != datetime(year, 4, 1).date()
                        ):
                            notify.send(
                                admin,
                                level="info",
                                timestamp=timestamp,
                                verb="Savings: Year End Balance",
                                recipient=User.objects.exclude(is_superuser=False),
                                description="End of year balance has been calculated.",
                            )

        except IntegrityError as e:
            return f"ERROR: Interest Calculation (OLD)\nERROR_DESC: {e}"
        else:
            return f"SUCCESS: Interest Calculation (OLD)"
