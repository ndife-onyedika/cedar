import csv
from datetime import time

from celery import shared_task
from django.db import IntegrityError, transaction
from django.utils import timezone
from django.utils.timezone import datetime
from notifications.signals import notify

from cedar.mixins import display_duration
from cedar.settings import STATIC_ROOT
from loans.models import LoanRequest
from savings.models import SavingsCredit, SavingsDebit
from settings.models import AccountChoice
from shares.models import Shares

from .models import Member, User


@shared_task
def check_activity():
    today = timezone.now()
    admin = User.objects.get(is_superuser=True)
    members = Member.objects.filter(is_active=True)
    recipients = User.objects.exclude(is_superuser=False)

    def _set_inactive(member):
        member.is_active = False
        member.save()
        notify.send(
            admin,
            level="error",
            recipients=recipients,
            verb="Account: Activity",
            description=f"{member.name} account has been set INACTIVE due to none operation for {display_duration(account_activity_duration)}.",
        )

    try:
        with transaction.atomic():
            for member in members:
                account_activity_duration = member.account_type.aad
                aad_days = account_activity_duration * 30
                last_savings_txn = SavingsCredit.objects.filter(
                    member=member, reason="credit-deposit"
                ).last()

                deposited_6mth = (
                    today.date() - last_savings_txn.created_at.date()
                ).days <= aad_days

                active_6mth = (
                    today.date() - member.date_joined.date()
                ).days <= aad_days
                if (
                    last_savings_txn
                    and not deposited_6mth
                    or not last_savings_txn
                    and active_6mth
                ):
                    _set_inactive(member)
    except IntegrityError as e:
        return f"ERROR: Member Activity Check Task!\nERROR_DESC: {e}"
    else:
        return f"SUCCESS: Member Activity Check Task!"


@shared_task
def import_csv():
    convert_amt = lambda amt: amt * 100
    is_null = lambda column: column.strip() == ""
    csv_urls = ["account_1.csv", "account_2.csv"]
    convert_date = lambda date: datetime.combine(
        datetime.strptime(date, "%d/%m/%Y").date(), time(9, 0)
    )

    try:
        with transaction.atomic():
            for url in csv_urls:
                csv_url = f"{STATIC_ROOT}doc/{url}"
                with open(csv_url) as csv_file:
                    csv_reader = csv.DictReader(csv_file)
                    for row in csv_reader:
                        if not is_null((name := row["NAME"])):
                            name = name.lower().split()
                            name = (
                                name[:-1]
                                if name[-1] == "***"
                                or name[-1] == "xxx"
                                or name[-1] == "****"
                                or name[-1] == "xxxx"
                                else name
                            )
                            acc_no = row["ACCOUNT NUMBER"]
                            name = " ".join([item.capitalize() for item in name])
                            year = acc_no.split("/")[2]
                            date_joined = datetime(year, 1, 1)
                            member = Member.objects.get_or_create(
                                name=name,
                                account_number=acc_no,
                                date_joined=date_joined,
                                account_type=AccountChoice.objects.get(
                                    name__icontains="Normal"
                                ),
                            )[0]
                            if not is_null(shares := row["SHARES"]):
                                date = datetime.combine(
                                    (
                                        convert_date(shares_date)
                                        if not is_null(
                                            shares_date := row["DATE (SHARES)"]
                                        )
                                        else date_joined
                                    ).date(),
                                    time(2, 0),
                                )
                                Shares.objects.get_or_create(
                                    member=member,
                                    amount=convert_amt(shares),
                                    created_at=date,
                                )
                            if not is_null(savings_credit := row["SAVINGS CREDIT"]):
                                date = convert_date(row["DATE (SAVINGS CREDIT)"])
                                savings = SavingsCredit.objects.get_or_create(
                                    member=member,
                                    created_at=date,
                                    reason="credit-deposit"
                                    if date != datetime(2014, 4, 1)
                                    else "credit-eoy",
                                )[0]
                                savings.amount += convert_amt(savings_credit)
                                savings.save()
                            if not is_null(savings_debit := row["SAVINGS DEBIT"]):
                                date = convert_date(row["DATE (SAVINGS DEBIT)"])
                                savings = SavingsDebit.objects.get_or_create(
                                    member=member,
                                    created_at=date,
                                    reason="debit-withdrawal",
                                )[0]
                                savings.amount += convert_amt(savings_debit)
                                savings.save()
                            if not is_null(loan := row["LOAN"]):
                                date = convert_date(row["DATE (SAVINGS DEBIT)"])
                                loan_amt = convert_amt(loan)
                                outstanding_amt = (
                                    convert_amt(out_amt)
                                    if not is_null(
                                        out_amt := row["OUTSTANDING PAYMENT (LOAN)"]
                                    )
                                    else loan_amt
                                )

                                interest = (
                                    (member.account_type.lir / 100)
                                    * loan_amt
                                    * member.account_type.ld
                                )
                                if outstanding_amt == loan_amt:
                                    outstanding_amt += interest

                                loan = LoanRequest.objects.create(
                                    member=member,
                                    created_at=date,
                                    amount=loan_amt,
                                    outstanding_amount=outstanding_amt,
                                )[0]
                                savings.amount += convert_amt(savings_debit)
                                savings.save()
    except IntegrityError as e:
        return f"ERROR: CSV Import Task!\nERROR_DESC: {e}"
    else:
        return f"SUCCESS: CSV Import Task!"
