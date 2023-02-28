from accounts.models import Member, User
from cedar.mixins import (
    get_amount,
    display_duration,
    months_between,
    get_last_day_month,
)
from django.utils.timezone import make_aware, datetime, timedelta, is_aware, now
from datetime import time

from notifications.signals import notify


def update_savings_total(member, date):
    from .models import SavingsInterest, SavingsTotal

    savings_intrs = SavingsInterest.objects.filter(
        member=member,
        disabled=False,
        created_at__date__lte=date.date(),
    ).order_by("created_at")
    total_amount = 0
    total_interest = 0
    if savings_intrs.count() > 0:
        for savings_intr in savings_intrs:
            total_interest += savings_intr.interest
            if savings_intr.is_comp:
                total_amount += savings_intr.amount
        savings_total = SavingsTotal.objects.get_or_create(member=member)[0]
        savings_total.amount = total_amount
        savings_total.interest = total_interest
        savings_total.updated_at = date
        savings_total.save()


def handle_withdrawal(context, instance):
    from .models import SavingsInterest

    member = instance.member
    amount = instance.amount
    date = instance.created_at

    savings_intrs = SavingsInterest.objects.filter(
        member=member, disabled=False, created_at__date__lte=date.date()
    )

    if context == "create":
        last_id = None
        remainder = 0
        withdrawal_amount = 0
        savings_intrs = savings_intrs.filter(is_comp=True).order_by("-created_at")
        for savings_intr in savings_intrs:
            if not withdrawal_amount >= amount:
                last_id = savings_intr.id
                withdrawal_amount += savings_intr.amount
                savings_intr.is_comp = False
                savings_intr.save()
        remainder = withdrawal_amount - amount
        if remainder > 0:
            intr = SavingsInterest.objects.get(id=last_id)
            intr.is_comp = True
            intr.amount = remainder
            intr.updated_at = date
            intr.save()
    elif context == "delete":
        savings_intrs = savings_intrs.filter(is_comp=False).order_by("-created_at")
        for savings_intr in savings_intrs:
            pass


def calculate_yearEndBalance(member, date_range: list):
    from .models import SavingsInterest, SavingsCredit

    end_date = make_aware(datetime.combine(date_range[1], time(2, 0)))
    date_range = [date_range[0], date_range[1] - timedelta(days=1)]

    savings_intrs = SavingsInterest.objects.filter(
        member=member, disabled=False, created_at__date__range=date_range
    )
    total_amount = 0
    total_interest = 0
    if savings_intrs.count() > 0:
        for savings_intr in savings_intrs:
            savings_intr.disabled = True
            total_interest += savings_intr.interest
            if savings_intr.is_comp:
                total_amount += savings_intr.amount
            savings_intr.save()

        sum_total = total_amount + total_interest

        SavingsCredit.objects.create(
            member=member, amount=sum_total, reason="credit-eoy", created_at=end_date
        )


def calculate_interest_exec(admin, member: Member, instance, date: datetime):
    interest_rate = member.account_type.sir / 100
    rate_day = interest_rate / 30

    if instance.start_comp:
        interest = instance.amount * rate_day
        instance.interest += interest
        instance.updated_at = date
        instance.save()
    else:
        pre_savings_interest_duration = member.account_type.psisd
        months_elapsed = int((date.date() - instance.created_at.date()).days / 30)
        is_eligible = months_elapsed >= pre_savings_interest_duration
        if is_eligible:
            instance.start_comp = True
            interest = instance.amount * interest_rate * months_elapsed
            notify.send(
                admin,
                level="info",
                timestamp=date,
                verb="Savings: Interest Started",
                recipient=User.objects.exclude(is_superuser=False),
                description="{} savings deposit of {} has past the {} period and started accumulating interest.".format(
                    member.name,
                    get_amount(instance.amount),
                    display_duration(pre_savings_interest_duration),
                ),
            )
            instance.interest += interest
            instance.updated_at = date
            instance.save()


def check_activity_exec(member, date: datetime):
    from savings.models import SavingsCredit

    admin = User.objects.get(is_superuser=True)
    recipients = User.objects.exclude(is_superuser=False)

    def _set_inactive(member, status: bool):
        is_active: bool = member.is_active
        member.is_active = status
        member.save()
        if is_active and not status:
            notify.send(
                admin,
                level="error",
                timestamp=date,
                recipient=recipients,
                verb="Account: Activity",
                description=f"{member.name} account has been set INACTIVE due to none operation for {display_duration(account_activity_duration)}.",
            )
        return status

    account_activity_duration = member.account_type.aad
    aad_days = account_activity_duration * 30
    last_savings_txn = SavingsCredit.objects.filter(
        member=member, reason="credit-deposit", created_at__date__lte=date.date()
    ).last()

    deposited_6mth = (
        (date.date() - last_savings_txn.created_at.date()).days <= aad_days
        if last_savings_txn
        else None
    )
    active_6mth = (date.date() - member.date_joined.date()).days >= aad_days
    if last_savings_txn and not deposited_6mth or not last_savings_txn and active_6mth:
        return _set_inactive(member, False)
    elif (
        last_savings_txn and deposited_6mth or not last_savings_txn and not active_6mth
    ):
        return _set_inactive(member, True)


def calculate_interest():
    from .models import SavingsInterest, SavingsDebit

    # members = Member.objects.filter(name__icontains="Abigail Adewumi")
    members = Member.objects.all()
    admin = User.objects.get(is_superuser=True)

    for year in range(2015, 2024):
        prev_year = year - 1
        start_date = datetime(prev_year, 4, 1).date()
        end_date = datetime(year, 4, 1).date()
        for month in months_between(start_date, end_date):
            for day in range(1, get_last_day_month(month.month, month.year) + 1):
                current_date = datetime.combine(
                    datetime(month.year, month.month, day), time(2, 0)
                )
                print(f"Count Timestamp: {current_date.date()}")
                if (
                    current_date.date() <= end_date
                    and current_date.date() <= now().date()
                ):
                    print(f"Working Timestamp: {current_date.date()}")
                    date_range = [start_date, current_date.date()]
                    for member in members:
                        if member.date_joined.date() <= current_date.date():
                            if current_date.date() < end_date:
                                is_active = check_activity_exec(member, current_date)
                                if is_active:
                                    savings = SavingsInterest.objects.filter(
                                        is_comp=True,
                                        member=member,
                                        disabled=False,
                                        created_at__date__range=date_range,
                                    )

                                    withdrawals = SavingsDebit.objects.filter(
                                        member=member,
                                        created_at__date=current_date.date(),
                                    )

                                    if savings.count() > 0:
                                        for saving in savings:
                                            calculate_interest_exec(
                                                admin=admin,
                                                member=member,
                                                instance=saving,
                                                date=make_aware(current_date),
                                            )

                                    if withdrawals.count() > 0:
                                        for withdrawal in withdrawals:
                                            handle_withdrawal(
                                                context="create", instance=withdrawal
                                            )
                            elif current_date.date() == end_date:
                                new_date_range = [start_date, end_date]
                                calculate_yearEndBalance(member, new_date_range)

                if current_date.date() == end_date:
                    notify.send(
                        admin,
                        level="info",
                        timestamp=current_date,
                        verb="Savings: Year End Balance",
                        recipient=User.objects.exclude(is_superuser=False),
                        description="End of year balance has been calculated.",
                    )
