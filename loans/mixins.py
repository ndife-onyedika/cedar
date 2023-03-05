from django.conf import settings as dj_sett
from django.contrib.sites.models import Site
from django.db import IntegrityError, transaction
from django.db.models.aggregates import Sum
from django.utils import timezone
from django.utils.timezone import timedelta
from accounts.models import User
from cedar.mixins import get_savings_total
from loans.models import LoanRequest

from notifications.signals import notify


def get_loan_details(loan: LoanRequest):
    due_date = loan.created_at.date() + timedelta(days=(loan.duration * 30))
    return {
        "dd": due_date,
    }


def check_loan_eligibility(member, amount):
    _percent = member.account_type.lsr / 100
    savings_total = get_savings_total(member).amount
    return savings_total >= (amount * _percent)


def task_exec(context, date):
    from .models import LoanRequest

    admin = User.objects.get(is_superuser=True)
    loans = LoanRequest.objects.filter(
        status="disbursed", created_at__isnull=False
    ).order_by("-created_at")
    reminders = {"due": due_reminder, "interest": calculate_loan_interests}
    reminders[context](admin, loans, date)


def due_reminder(admin, loans, date):
    if loans.count() > 0:
        for loan in loans:
            member = loan.member
            due_date = get_loan_details(loan)["due_date"]
            is_2days = (due_date - date.date()) == 2
            is_7days = (due_date - date.date()) == 7

            if is_2days or is_7days:
                notify.send(
                    admin,
                    level="info",
                    verb=f"Loan: Due Date - {member.name}",
                    recipient=User.objects.exclude(is_superuser=False),
                    description="{}'s loan is due in {} days time".format(
                        member.name, 2 if is_2days else 7
                    ),
                )

            if date.date() == due_date and loan.outstanding_amount > 0:
                member.is_active = False
                member.save()
                notify.send(
                    admin,
                    level="error",
                    verb=f"Loan: Loan Repayment Past Due - {member.name}",
                    recipient=User.objects.exclude(is_superuser=False),
                    description=f"{loan.member.name} account has been set INACTIVE due the inability to pay up loan at stipulated time.",
                )


def calculate_loan_interests(admin, loans, date):
    if loans.count() > 0:
        for loan in loans:
            duration = loan.duration
            interest_rate = loan.interest_rate / 100
            outstanding_amount = loan.outstanding_amount
            months_elapsed = int((date.date() - loan.created_at.date()).days / 30)
            if months_elapsed <= duration:
                interest = (interest_rate / 30) * (duration / 12) * loan.amount
                outstanding_amount += interest
                loan.outstanding_amount = outstanding_amount
                loan.save()
