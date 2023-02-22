from django.db import models
from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch.dispatcher import receiver
from django.utils import timezone

from accounts.models import Member
from cedar.constants import CREDIT_REASON_CHOICES, DEBIT_REASON_CHOICES
from cedar.mixins import CustomAbstractTable
from savings.mixins import handle_withdrawal, update_savings_total


# Create your models here.
class Savings(models.Model):
    member = models.ForeignKey(Member, on_delete=models.CASCADE)
    amount = models.BigIntegerField(default=0)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        abstract = True


class SavingsCredit(Savings):
    reason = models.CharField(
        "Reason for Credit",
        max_length=50,
        default="credit-deposit",
        choices=CREDIT_REASON_CHOICES,
    )

    class Meta:
        verbose_name_plural = "Savings Credit"


class SavingsDebit(Savings):
    reason = models.CharField(
        "Reason for Debit",
        max_length=50,
        default="debit-withdrawal",
        choices=DEBIT_REASON_CHOICES,
    )

    class Meta:
        verbose_name_plural = "Savings Debit"


class SavingsTotal(CustomAbstractTable):
    member = models.OneToOneField(Member, on_delete=models.CASCADE)
    interest = models.BigIntegerField(default=0)

    class Meta:
        verbose_name_plural = "Savings Total"


class YearEndBalance(CustomAbstractTable):
    member = models.ForeignKey(Member, on_delete=models.CASCADE)
    updated_at = None

    class Meta:
        verbose_name = "Year End Balance"
        verbose_name_plural = "Year End Balances"


class SavingsInterest(Savings):
    savings = models.OneToOneField(SavingsCredit, on_delete=models.CASCADE)
    interest = models.BigIntegerField(default=0)
    is_comp = models.BooleanField("Is Compounding?", default=True)
    start_comp = models.BooleanField("Started Compounding?", default=False)
    disabled = models.BooleanField(default=False)
    updated_at = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = "Savings Interest"
        verbose_name_plural = "Savings Interests"


@receiver(post_save, sender=SavingsCredit)
def post_savings_credit_save(sender, instance: SavingsCredit, **kwargs):
    if kwargs["created"]:
        SavingsInterest.objects.create(
            savings=instance,
            member=instance.member,
            amount=instance.amount,
            created_at=instance.created_at,
            updated_at=instance.created_at,
        )
        if instance.reason == "credit-eoy":
            YearEndBalance.objects.create(
                member=instance.member,
                amount=instance.amount,
                created_at=instance.created_at,
            )


@receiver(post_delete, sender=SavingsCredit)
def post_savings_credit_delete(sender, instance: SavingsCredit, **kwargs):
    if instance.reason == "credit-eoy":
        YearEndBalance.objects.filter(
            member=instance.member,
            amount=instance.amount,
            created_at=instance.created_at,
        ).delete()


@receiver(post_save, sender=SavingsDebit)
def post_savings_debit_save(sender, instance: SavingsDebit, **kwargs):
    if kwargs["created"]:
        handle_withdrawal(context="create", instance=instance)


@receiver(post_delete, sender=SavingsDebit)
def post_savings_debit_delete(sender, instance: SavingsDebit, **kwargs):
    handle_withdrawal(context="delete", instance=instance)


@receiver(post_save, sender=SavingsInterest)
def post_savings_interest_save(sender, instance: SavingsInterest, **kwargs):
    update_savings_total(member=instance.member, date=instance.created_at)


@receiver(post_delete, sender=SavingsInterest)
def post_savings_interest_delete(sender, instance: SavingsInterest, **kwargs):
    update_savings_total(member=instance.member, date=instance.created_at)
