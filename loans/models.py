from django.db import models

from accounts.models import Member, User
from cedar.constants import LOAN_STATUS_CHOICES
from django.utils import timezone

from django.db import IntegrityError, models, transaction
from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch.dispatcher import receiver
from notifications.signals import notify

from cedar.mixins import get_amount


# Create your models here.
class LoanRequest(models.Model):
    member = models.ForeignKey(Member, on_delete=models.CASCADE)
    amount = models.BigIntegerField(default=0)
    outstanding_amount = models.BigIntegerField(default=0)

    duration = models.IntegerField()
    interest_rate = models.FloatField()
    status = models.CharField(max_length=50, choices=LOAN_STATUS_CHOICES)

    guarantor_1 = models.ForeignKey(
        Member, null=True, related_name="guarantor_1", on_delete=models.SET_NULL
    )
    guarantor_2 = models.ForeignKey(
        Member, null=True, related_name="guarantor_2", on_delete=models.SET_NULL
    )

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)
    terminated_at = models.DateTimeField()


class LoanRepayment(models.Model):
    member = models.ForeignKey(Member, on_delete=models.CASCADE)
    loan = models.ForeignKey(LoanRequest, on_delete=models.CASCADE)
    amount = models.BigIntegerField(default=0)

    created_at = models.DateTimeField(default=timezone.now)


@receiver(post_save, sender=LoanRequest)
def post_loan_save(sender, instance: LoanRequest, **kwargs):
    admin = User.objects.get(is_superuser=True)
    if instance.status == "terminated" and not instance.terminated_at:
        instance.terminated_at = timezone.now()
        instance.save()
        notify.send(
            admin,
            level="info",
            verb="Loan: Termination",
            recipients=User.objects.exclude(is_superuser=False),
            description="{}'s loan has completed payment for loan and is hereby terminated.".format(
                instance.member.name
            ),
        )


@receiver(post_save, sender=LoanRepayment)
def post_loan_repay_save(sender, instance: LoanRepayment, **kwargs):
    if kwargs["created"]:
        member = instance.member
        admin = User.objects.get(is_superuser=True)
        try:
            with transaction.atomic():
                loan = instance.loan
                outstanding_amount = loan.outstanding_amount
                outstanding_amount -= instance.amount
                loan.outstanding_amount = outstanding_amount
                if outstanding_amount == 0:
                    loan.status = "terminated"
                loan.save()
                notify.send(
                    admin,
                    level="info",
                    verb="Loan: Repayment",
                    recipients=User.objects.exclude(is_superuser=False),
                    description="{} has made a repayment of {} for his/her {} loan. Outstanding Balance is {}.".format(
                        member.name,
                        get_amount(instance.amount),
                        get_amount(instance.loan.amount),
                        get_amount(instance.loan.outstanding_amount),
                    ),
                )
        except IntegrityError as e:
            return f"LOAN-REPAYMENT-MODEL-ERROR: {e}"
