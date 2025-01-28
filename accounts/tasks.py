import csv
import logging
from datetime import time

from celery import shared_task
from django.db import IntegrityError, transaction
from django.utils import timezone
from django.utils.timezone import datetime, make_aware
from notifications.signals import notify

from cedar.mixins import display_duration
from cedar.settings import STATIC_ROOT
from loans.models import LoanRepayment, LoanRequest
from savings.mixins import check_activity_exec
from savings.models import SavingsCredit, SavingsDebit
from settings.models import AccountChoice
from shares.models import Shares

from .models import Member, NextOfKin, User

logger = logging.getLogger(__name__)


@shared_task
def check_activity():
    today = timezone.now()
    members = Member.objects.filter(is_active=True)

    try:
        with transaction.atomic():
            for member in members:
                check_activity_exec(member, today)
    except IntegrityError as e:
        error = f"ERROR: Member Activity Check Task!\nERROR_DESC: {e}"
        logger.error(error, exc_info=1)
        return error
    return f"SUCCESS: Member Activity Check Task!"


@shared_task
def import_csv():
    convert_amt = lambda amt: float(amt) * 100
    is_null = lambda column: column.strip() == ""
    csv_urls = ["TEMPLATE1.csv", "TEMPLATE2.csv", "TEMPLATE3.csv"]
    convert_date = lambda date: make_aware(
        datetime.combine(datetime.strptime(date, "%d/%m/%Y").date(), time(9, 0))
    )

    try:
        with transaction.atomic():
            for url in csv_urls:
                csv_url = f"{STATIC_ROOT}/doc/{url}"
                with open(csv_url) as csv_file:
                    csv_reader = csv.DictReader(csv_file)
                    for row in csv_reader:
                        if not is_null((name := row["NAME"])):
                            name = name.lower().split()
                            name = name[:-1] if name[-1] == "xxx" else name
                            acc_no = row["ACCOUNT NUMBER"]
                            name = " ".join([item.capitalize() for item in name])
                            print(name)
                            year = int(acc_no.split("/")[2])
                            year = (2000 if not year > 23 else 1900) + year
                            date_joined = make_aware(datetime(year, 1, 1))
                            member = Member.objects.get_or_create(
                                name=name,
                                account_number=acc_no,
                                date_joined=date_joined,
                                account_type=AccountChoice.objects.get(
                                    name__icontains="Normal"
                                ),
                            )[0]
                            NextOfKin.objects.get_or_create(member=member)
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
                                    created_at=make_aware(date),
                                )
                            if name.lower() not in ("longinus amuchie",):
                                if not is_null(savings_credit := row["SAVINGS CREDIT"]):
                                    date = convert_date(row["DATE (SAVINGS CREDIT)"])
                                    if date.date() != datetime(2014, 4, 1).date():
                                        reason = "credit-deposit"
                                    else:
                                        reason = "credit-eoy"
                                    savings = SavingsCredit.objects.get_or_create(
                                        member=member, reason=reason, created_at=date
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
                                    date = (
                                        convert_date(row["DATE (LOAN)"])
                                        if not is_null(row["DATE (LOAN)"])
                                        else None
                                    )
                                    loan_amt = convert_amt(loan)
                                    outstanding_amt = (
                                        convert_amt(out_amt)
                                        if row.get("OUTSTANDING PAYMENT (LOAN)")
                                        and not is_null(
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
                                        duration=6,
                                        member=member,
                                        interest_rate=4,
                                        created_at=date,
                                        amount=loan_amt,
                                        outstanding_amount=outstanding_amt,
                                    )
                                    # if not is_null(loan := row["LOAN REPAY"]):
                                    #     loan_repay = LoanRepayment.objects.create(
                                    #         loan=loan,
                                    #         member=member,
                                    #         created_at=convert_date(
                                    #             row["DATE (LOAN REPAY)"]
                                    #         ),
                                    #         amount=convert_amt(row["LOAN REPAY"]),
                                    #     )
    except IntegrityError as e:
        error = f"ERROR: CSV Import Task!\nERROR_DESC: {e}"
        logger.error(error, exc_info=1)
        return error
    return f"SUCCESS: CSV Import Task!"
