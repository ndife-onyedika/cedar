from re import T

from django.db import IntegrityError, models, transaction
from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch.dispatcher import receiver
from django.utils import timezone
from notifications.signals import notify

from accounts.models import Member, User
from cedar.constants import LOAN_STATUS_CHOICES
from cedar.mixins import (
    display_duration,
    display_rate,
    get_amount,
    get_data_equivalent,
    format_date_model,
)


# Create your models here.
class LoanRequest(models.Model):
    member = models.ForeignKey(Member, on_delete=models.CASCADE)
    amount = models.BigIntegerField(default=0)
    outstanding_amount = models.BigIntegerField(default=0)

    duration = models.IntegerField()
    interest_rate = models.FloatField()
    status = models.CharField(
        max_length=50, choices=LOAN_STATUS_CHOICES, default="disbursed"
    )

    guarantor_1 = models.ForeignKey(
        Member, null=True, related_name="guarantor_1", on_delete=models.SET_NULL
    )
    guarantor_2 = models.ForeignKey(
        Member, null=True, related_name="guarantor_2", on_delete=models.SET_NULL
    )

    created_at = models.DateTimeField(default=timezone.now, blank=True, null=True)
    updated_at = models.DateTimeField(default=timezone.now, blank=True, null=True)
    terminated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        verbose_name_plural = "Loan Requests"

    def __str__(self):
        return "({}, {}, {}, {}, {}, {}, {}, {})".format(
            self.member.name,
            get_amount(self.amount),
            get_amount(self.outstanding_amount),
            display_duration(self.duration),
            display_rate(self.interest_rate),
            get_data_equivalent(self.status, "lsc"),
            format_date_model(self.created_at),
            format_date_model(self.updated_at),
        )


class LoanRepayment(models.Model):
    member = models.ForeignKey(Member, on_delete=models.CASCADE)
    loan = models.ForeignKey(LoanRequest, on_delete=models.CASCADE)
    amount = models.BigIntegerField(default=0)

    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name_plural = "Loan Repayments"

    def __str__(self):
        return "({}, {}, {}, {})".format(
            self.member.name,
            self.__str__(),
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
    if kwargs["created"]:
        try:
            with transaction.atomic():
                loan = instance.loan
                outstanding_amount = loan.outstanding_amount
                outstanding_amount -= instance.amount
                loan.outstanding_amount = outstanding_amount
                if outstanding_amount == 0:
                    loan.status = "terminated"
                loan.save()
        except IntegrityError as e:
            return f"LOAN-REPAYMENT-MODEL-ERROR: {e}"
