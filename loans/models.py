import re
from re import T

from django.db import IntegrityError, models, transaction
from django.db.models.aggregates import Sum
from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch.dispatcher import receiver
from django.utils import timezone
from notifications.signals import notify

from accounts.models import Member, User
from utils.choices import LoanStatusChoice
from utils.helpers import display_duration, display_rate, format_date_model, get_amount


# Create your models here.
class LoanRequest(models.Model):
    member = models.ForeignKey(Member, on_delete=models.CASCADE)
    amount = models.BigIntegerField(default=0)
    outstanding_amount = models.BigIntegerField(default=0)

    duration = models.IntegerField()
    interest_rate = models.FloatField()
    status = models.CharField(
        max_length=50,
        choices=LoanStatusChoice.choices,
        default=LoanStatusChoice.DISBURSED,
    )
    guarantors = models.ManyToManyField(
        Member, blank=True, related_name="loan_guarantors"
    )

    created_at = models.DateTimeField(default=timezone.now, blank=True, null=True)
    updated_at = models.DateTimeField(default=timezone.now, blank=True, null=True)
    terminated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name_plural = "Loan Requests"

    def __str__(self):
        return "({}, {}, {}, {}, {}, {}, {}, {})".format(
            self.member.name,
            self.amount_display,
            self.outstanding_amount_display,
            self.duration_display,
            self.interest_rate_display,
            self.status_display,
            format_date_model(self.created_at),
            format_date_model(self.updated_at),
        )

    @property
    def status_display(self):
        return self.get_status_display()

    @property
    def duration_display(self):
        return display_duration(self.duration)

    @property
    def interest_rate_display(self):
        return display_rate(self.interest_rate)

    @property
    def amount_display(self):
        return get_amount(self.amount)

    @property
    def outstanding_amount_display(self):
        return get_amount(self.outstanding_amount)


class LoanRepayment(models.Model):
    member = models.ForeignKey(Member, on_delete=models.CASCADE)
    loan = models.ForeignKey(LoanRequest, on_delete=models.CASCADE)
    amount = models.BigIntegerField(default=0)

    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-created_at"]
        verbose_name_plural = "Loan Repayments"

    def __str__(self):
        return "({}, {}, {}, {})".format(
            self.member.name,
            self.loan.__str__(),
            get_amount(self.amount),
            format_date_model(self.created_at),
        )


@receiver(post_save, sender=LoanRequest)
def post_loan_save(sender, instance: LoanRequest, **kwargs):
    admin = User.objects.get(is_superuser=True)
    if kwargs["created"]:
        instance.outstanding_amount = instance.amount
        instance.save()

    if instance.status == "terminated" and not instance.terminated_at:
        instance.terminated_at = timezone.now()
        instance.save()
        notify.send(
            admin,
            level="info",
            timestamp=timezone.now(),
            verb=f"Loan: Termination - {instance.member.name}",
            recipient=User.objects.exclude(is_superuser=False),
            description="{}'s loan has completed payment for loan and is hereby terminated.".format(
                instance.member.name
            ),
        )


@receiver(post_save, sender=LoanRepayment)
def post_loan_repay_save(sender, instance: LoanRepayment, **kwargs):
    try:
        with transaction.atomic():
            loan = instance.loan
            total = (
                loan.loanrepayment_set.all().aggregate(Sum("amount"))["amount__sum"]
                or 0
            )
            outstanding_amount = loan.amount - total
            loan.outstanding_amount = outstanding_amount
            if loan.status == "disbursed" and outstanding_amount == 0:
                loan.status = "terminated"
            loan.save()
    except IntegrityError as e:
        return f"LOAN-REPAYMENT-MODEL-ERROR: {e}"


@receiver(post_delete, sender=LoanRepayment)
def post_loan_repay_delete(sender, instance: LoanRepayment, **kwargs):
    try:
        with transaction.atomic():
            loan = instance.loan
            total = (
                loan.loanrepayment_set.all().aggregate(Sum("amount"))["amount__sum"]
                or 0
            )
            outstanding_amount = loan.amount + total
            loan.outstanding_amount = outstanding_amount
            if loan.status == "terminated" and outstanding_amount != 0:
                loan.status = "disbursed"
            loan.save()
    except IntegrityError as e:
        return f"LOAN-REPAYMENT-MODEL-ERROR: {e}"
