import base64
import calendar
import json
import os
from functools import lru_cache

import jwt
import redis
from django.conf import settings as dj_sett
from django.core.files.base import File
from django.db import IntegrityError, OperationalError, models, transaction
from django.db.models.aggregates import Sum
from django.utils import timezone
from django.utils.timezone import datetime
from docxtpl import DocxTemplate

from .constants import (
    CREDIT_REASON_CHOICES,
    DEBIT_REASON_CHOICES,
    LOAN_STATUS_CHOICES,
    RELATIONSHIP_CHOICE,
)


redis_instance = redis.StrictRedis(
    host=dj_sett.REDIS_HOST, port=dj_sett.REDIS_PORT, db=0
)


get_last_day_month = lambda month, year: calendar.monthrange(year, month)[1]

check_day_valid = lambda day, month, year: day <= get_last_day_month(month, year)

member_preferred_currency = lambda member: member.preference.currency

currency_abbr = lambda currency: currency.abbr.lower()

return_month_int = lambda _month: int(
    _month.lower().replace("months", "").replace("month", "").strip()
)

convert_month_2_days = (
    lambda _month: f"{(return_month_int(_month=_month) * 30)} days"
    if _month and _month != "-"
    else "-"
)
display_duration = lambda duration: f"{duration} Month{'s' if duration > 1 else ''}"
display_rate = lambda rate: f"{rate}%"
format_date_model = (
    lambda date: datetime.strftime(date, "%d %b %y") if not date is None else "-"
)


def create_tables(member):
    from savings.models import SavingsTotal
    from shares.models import SharesTotal

    SavingsTotal.objects.get_or_create(member=member, created_at=member.date_joined)
    SharesTotal.objects.get_or_create(member=member, created_at=member.date_joined)


def get_savings_total(member):
    from savings.models import SavingsTotal

    return SavingsTotal.objects.get_or_create(member=member)[0].amount


def get_shares_total(member):
    from shares.models import SharesTotal

    return SharesTotal.objects.get_or_create(member=member)[0].amount


def convert_date(data, context):
    if context == "str":
        result = data.strftime("%Y-%m-%d")
    elif context == "date":
        result = datetime.strptime(data, "%Y-%m-%d").date()

    return result


def get_account_choices(form=True) -> list:
    from settings.models import AccountChoice

    ACC_CHOICES = [(None, "Select Account Type")] if form else []
    db_acc_choices = AccountChoice.objects.all()
    try:
        acc_choices = (
            ACC_CHOICES
            + [(choice.id, f"{choice.name} Member") for choice in db_acc_choices]
            if db_acc_choices.count() > 0
            else ACC_CHOICES
        )
    except OperationalError:
        acc_choices = ACC_CHOICES

    return acc_choices


def get_member_choices(form=True) -> list:
    from accounts.models import Member

    MEM_CHOICES = [(None, "Select Member")] if form else []
    db_member_choices = Member.objects.all()
    try:
        acc_choices = (
            MEM_CHOICES
            + [
                (
                    choice.id,
                    "{} ({})".format(
                        choice.name, "Active" if choice.is_active else "Inactive"
                    ),
                )
                for choice in db_member_choices
            ]
            if db_member_choices.count() > 0
            else MEM_CHOICES
        )
    except OperationalError:
        acc_choices = MEM_CHOICES

    return acc_choices


def convert_month_2_year(_month):
    _year = return_month_int(_month=_month) / 12
    _year = int(_year) if not str(_year).find(".") > -1 else round(_year, 1)

    return _year


def get_loan_status_info(context, **kwargs):
    from cedar.constants import LOAN_STATUS_CHOICES

    if context == "check":
        data = False
        if kwargs["status"] in list(map(lambda status: status[0], LOAN_STATUS_CHOICES)):
            data = True
        return data
    else:
        data = []
        for loan in LOAN_STATUS_CHOICES:
            data.append({"name": loan[1], "name_short": loan[0]})
        return data


def loan_eligibility(member, amount):
    savings_total = get_savings_total(member)
    return savings_total >= (member.account_type.lsp / 100) * amount


def get_amount(amount):
    amount = amount if amount else 0
    return "{}{:,}".format("\u20A6", round(float(amount / 100), 2))


def get_data_equivalent(data, context):
    # TODO:this is still very error prone as a small mistake in key name will result to unwanted results and the dictionary
    # might become extremly large overtime for such large choices : what is really important here is the later operations
    # on your word i'll remove this and find where they are used and fix stuff
    choices_ = {
        "rc": RELATIONSHIP_CHOICE,
        "lsc": LOAN_STATUS_CHOICES,
        "src": CREDIT_REASON_CHOICES + DEBIT_REASON_CHOICES,
    }

    choices = choices_[context]
    # NOTE:json.dumps(choices) is done because lru_cache only accept hashable object to store in cache
    data_str = human_readable_string_frm_tuple_list(data, json.dumps(choices))

    if not data_str:
        return " ".join([data_item.capitalize() for data_item in data.split("-")])

    return data_str


@lru_cache(maxsize=1000)
def human_readable_string_frm_tuple_list(data, tuple_list_str):
    tuple_list = json.loads(tuple_list_str)
    for tuple_ in tuple_list:
        if data == tuple_[0]:
            return tuple_[1]
    return ""


def get_interval(seconds):
    from django_celery_beat.models import IntervalSchedule

    return IntervalSchedule.objects.get_or_create(
        every=seconds, period=IntervalSchedule.SECONDS
    )[0]


def get_crontab(minute, hour, day_of_month, month_of_year):
    from django_celery_beat.models import CrontabSchedule

    return CrontabSchedule.objects.get_or_create(
        hour=hour,
        minute=minute,
        day_of_month=day_of_month,
        timezone=dj_sett.TIME_ZONE,
        month_of_year=month_of_year,
    )[0]


def email_me_prod(subject, body):
    from django.core.mail.message import EmailMessage

    html_email = EmailMessage(subject=subject, body=body, to=[dj_sett.MAIL_DEV])
    html_email.content_subtype = "html"
    html_email.send()


def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i : i + n]


def send_mass_html_mail(datalist, context):
    from .tasks import send_mail

    """
    Given a datatuple of (subject, text_content, html_content, from_email,
    recipient_list), sends each message to each recipient list. Returns the
    number of emails sent.

    If from_email is None, the DEFAULT_FROM_EMAIL setting is used.
    If auth_user and auth_password are set, they're used to log in.
    If auth_user is None, the EMAIL_HOST_USER setting is used.
    If auth_password is None, the EMAIL_HOST_PASSWORD setting is used.

    """
    countdown = 0
    if context == "single":
        send_mail.apply_async([datalist], countdown=countdown)
    elif context == "mass":
        for splitted_message in list(chunks(lst=datalist, n=20)):
            countdown += 5
            send_mail.apply_async([splitted_message], countdown=countdown)


class CustomAbstractTable(models.Model):
    amount = models.BigIntegerField(default=0)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)

    class Meta:
        abstract = True


class HandleAtomicTransactionException:
    def __init__(self, txn_func, exception_cls, message) -> None:
        self.transaction_function = txn_func
        self.exception_class = exception_cls
        self.message = message
        self._result = None

    def perform_transaction(self):
        try:
            with transaction.atomic():
                self._result = self.transaction_function()
        except self.exception_class as e:
            raise self.exception_class(f"{self.message}: {e}")

    def get_result(self):
        return self._result


def custom_celery_task(interval: int, name: str, task: str, data: list) -> None:
    from django_celery_beat.models import PeriodicTask

    _task = PeriodicTask.objects.get_or_create(
        task=task,
        one_off=True,
        name=f"{name}_{interval}sec",
        interval=get_interval(seconds=interval),
    )[0]
    _task.args = json.dumps(data)
    _task.enabled = True
    _task.save()


def file_cleanup(path):
    """
    File cleanup callback used to emulate the old delete
    behavior using signals. Initially django deleted linked
    files when an object containing a File/ImageField was deleted.

    Usage:
    >>> from django.db.models.signals import post_delete
    >>> post_delete.connect(file_cleanup, sender=MyModel, dispatch_uid="mymodel.file_cleanup")
    """
    """ Deletes file from filesystem. """
    if os.path.isfile(path):
        os.remove(path)


class TokenGenerator:
    def __init__(self) -> None:
        self._secret = dj_sett.SECRET_KEY
        self._algorithm = "HS256"

    def make_token(self, email, expiration=timezone.timedelta(minutes=10), **kwargs):
        """
        Generate JWT that expires in X minutes
        """
        return jwt.encode(
            {
                "email": email,
                "exp": timezone.now() + expiration,
                **kwargs,
            },
            self._secret,
            algorithm=self._algorithm,
        )

    def check_token(self, token):
        try:
            decoded = jwt.decode(token, self._secret, algorithms=[self._algorithm])
        except Exception as e:
            print(e)
            return False
        else:
            return decoded


def get_daycount_nextdate(date, month_count, **kwargs):
    start_date = date
    year = start_date.year
    next_month = start_date.month + month_count

    if not next_month > 12:
        month = next_month
    else:
        while next_month > 12:
            next_month -= 12
            year += 1

        month = next_month

    day = start_date.day
    end_date = (
        datetime(year, month, day).date()
        if not kwargs or not kwargs.get("day_count_b4_pay")
        else (
            datetime(year, month, day).date()
            - timezone.timedelta(days=kwargs["day_count_b4_pay"])
        )
    )

    data = end_date - start_date

    return data


def months_between(start_date, end_date):
    """
    Given two instances of ``datetime.date``, generate a list of dates on
    the 1st of every month between the two dates (inclusive).

    e.g. "5 Jan 2020" to "17 May 2020" would generate:

        1 Jan 2020, 1 Feb 2020, 1 Mar 2020, 1 Apr 2020, 1 May 2020

    """
    if start_date > end_date:
        raise ValueError(f"Start date {start_date} is not before end date {end_date}")

    year = start_date.year
    month = start_date.month

    while (year, month) <= (end_date.year, end_date.month):
        yield datetime(year, month, 1).date()

        # Move to the next month.  If we're at the end of the year, wrap around
        # to the start of the next.
        #
        # Example: Nov 2017
        #       -> Dec 2017 (month += 1)
        #       -> Jan 2018 (end of year, month = 1, year += 1)
        #
        if month == 12:
            month = 1
            year += 1
        else:
            month += 1
