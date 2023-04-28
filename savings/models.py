from django.db import models
from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch.dispatcher import receiver
from django.utils import timezone

from accounts.models import Member
from cedar.constants import CREDIT_REASON_CHOICES, DEBIT_REASON_CHOICES
from cedar.mixins import (
    CustomAbstractTable,
    get_amount,
    format_date_model,
    get_data_equivalent,
    get_savings_total,
)
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

    def __str__(self):
        return "SC({}, {}, {}, {})".format(
            self.member.name,
            get_amount(self.amount),
            get_data_equivalent(self.reason, "src"),
            format_date_model(self.created_at),
        )


class SavingsDebit(Savings):
    reason = models.CharField(
        "Reason for Debit",
        max_length=50,
        default="debit-withdrawal",
        choices=DEBIT_REASON_CHOICES,
    )

    class Meta:
        verbose_name_plural = "Savings Debit"

    def __str__(self):
        return "SD({}, {}, {}, {})".format(
            self.member.name,
            get_amount(self.amount),
            get_data_equivalent(self.reason, "src"),
            format_date_model(self.created_at),
        )


class SavingsTotal(CustomAbstractTable):
    member = models.OneToOneField(Member, on_delete=models.CASCADE)
    interest = models.BigIntegerField(default=0)

    class Meta:
        verbose_name_plural = "Savings Total"

    def __str__(self):
        return "ST({}, {}, {}, {}, {})".format(
            self.member.name,
            get_amount(self.amount),
            get_amount(self.interest),
            format_date_model(self.created_at),
            format_date_model(self.updated_at),
        )


class YearEndBalance(CustomAbstractTable):
    member = models.ForeignKey(Member, on_delete=models.CASCADE)
    updated_at = None

    class Meta:
        verbose_name = "Year End Balance"
        verbose_name_plural = "Year End Balances"

    def __str__(self):
        return "YEB({}, {}, {})".format(
            self.member.name,
            get_amount(self.amount),
            format_date_model(self.created_at),
        )


class SavingsInterest(Savings):
    savings = models.ForeignKey(SavingsCredit, on_delete=models.CASCADE)
    interest = models.BigIntegerField(default=0)
    total_interest = models.BigIntegerField(default=0)

    class Meta:
        verbose_name_plural = "Savings Interests"

    def __str__(self):
        return "SI({}, {}, {}, {}, {}, {})".format(
            self.member.name,
            self.savings.__str__(),
            get_amount(self.amount),
            get_amount(self.interest),
            get_amount(self.total_interest),
            format_date_model(self.created_at),
        )


class SavingsInterestTotal(Savings):
    savings = models.OneToOneField(SavingsCredit, on_delete=models.CASCADE)
    interest = models.BigIntegerField(default=0)
    is_comp = models.BooleanField("Is Compounding?", default=True)
    start_comp = models.BooleanField("Started Compounding?", default=False)
    disabled = models.BooleanField(default=False)
    updated_at = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name_plural = "Savings Interests Total"

    def __str__(self):
        return "SIT({}, {}, {}, {}, is: {}, sc: {}, dis: {}, {}, {})".format(
            self.member.name,
            self.savings.__str__(),
            get_amount(self.amount),
            get_amount(self.interest),
            self.is_comp,
            self.start_comp,
            self.disabled,
            format_date_model(self.created_at),
            format_date_model(self.updated_at),
        )


# class TotalInterest(CustomAbstractTable):
#     member = models.OneToOneField(Member, on_delete=models.CASCADE)
#     interest = models.BigIntegerField(default=0)

#     class Meta:
#         verbose_name = "Total Interest"
#         verbose_name_plural = "Total Interests"


@receiver(post_save, sender=SavingsCredit)
def post_savings_credit_save(sender, instance: SavingsCredit, **kwargs):
    si = SavingsInterestTotal.objects.get_or_create(
        savings=instance, member=instance.member, created_at=instance.created_at
    )[0]
    si.amount = instance.amount
    si.updated_at = instance.created_at
    # si.updated_at = timezone.now()
    if instance.reason == "credit-eoy":
        si.start_comp = True
        eoy = YearEndBalance.objects.get_or_create(
            member=instance.member,
            created_at=instance.created_at,
        )[0]
        if eoy.amount != instance.amount:
            eoy.amount += instance.amount
            eoy.save()
    si.save()


# @receiver(post_delete, sender=SavingsCredit)
def post_savings_credit_delete(sender, instance: SavingsCredit, **kwargs):
    if instance.reason == "credit-eoy":
        YearEndBalance.objects.filter(
            member=instance.member,
            amount=instance.amount,
            created_at=instance.created_at,
        ).delete()


# @receiver(post_save, sender=SavingsDebit)
def post_savings_debit_save(sender, instance: SavingsDebit, **kwargs):
    if kwargs["created"]:
        handle_withdrawal(context="create", instance=instance)


# @receiver(post_delete, sender=SavingsDebit)
def post_savings_debit_delete(sender, instance: SavingsDebit, **kwargs):
    handle_withdrawal(context="delete", instance=instance)


@receiver(post_save, sender=SavingsInterestTotal)
def post_savings_interest_total_save(sender, instance: SavingsInterestTotal, **kwargs):
    update_savings_total(member=instance.member)


@receiver(post_delete, sender=SavingsInterestTotal)
def post_savings_interest_total_delete(
    sender, instance: SavingsInterestTotal, **kwargs
):
    update_savings_total(member=instance.member)
