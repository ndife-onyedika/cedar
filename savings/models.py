from django.db import models
from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch.dispatcher import receiver
from django.utils import timezone

from accounts.models import Member
from savings.utils.helpers import handle_withdrawal, update_savings_total
from utils.choices import CreditReasonChoice, DebitReasonChoice
from utils.helpers import CustomAbstractTable, format_date_model, get_amount


# Create your models here.
class Savings(models.Model):
    member = models.ForeignKey(Member, on_delete=models.CASCADE)
    amount = models.BigIntegerField(default=0)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        abstract = True

    @property
    def amount_display(self):
        return get_amount(self.amount)

    @property
    def reason_display(self):
        choices = CreditReasonChoice.choices + DebitReasonChoice.choices
        for choice in choices:
            if self.reason == choice[0]:
                return choice[1]
        return ""


class SavingsCredit(Savings):
    reason = models.CharField(
        "Reason for Credit",
        max_length=50,
        choices=CreditReasonChoice.choices,
        default=CreditReasonChoice.DEPOSIT,
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name_plural = "Savings Credit"

    def __str__(self):
        return "SC({}, {}, {}, {})".format(
            self.member.name,
            self.amount_display,
            self.reason_display,
            format_date_model(self.created_at),
        )


class SavingsDebit(Savings):
    reason = models.CharField(
        "Reason for Debit",
        max_length=50,
        choices=DebitReasonChoice.choices,
        default=DebitReasonChoice.WITHDRAWAL,
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name_plural = "Savings Debit"

    def __str__(self):
        return "SD({}, {}, {}, {})".format(
            self.member.name,
            self.amount_display,
            self.reason_display,
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
            self.amount_display,
            self.interest_display,
            format_date_model(self.created_at),
            format_date_model(self.updated_at),
        )

    @property
    def interest_display(self):
        return get_amount(self.interest)


class YearEndBalance(CustomAbstractTable):
    member = models.ForeignKey(Member, on_delete=models.CASCADE)
    updated_at = None

    class Meta:
        verbose_name = "Year End Balance"
        verbose_name_plural = "Year End Balances"
        ordering = ["-created_at", "member__name"]

    def __str__(self):
        return "YEB({}, {}, {})".format(
            self.member.name,
            self.amount_display,
            format_date_model(self.created_at),
        )


class SavingsInterest(Savings):
    savings = models.ForeignKey(SavingsCredit, on_delete=models.CASCADE)
    interest = models.BigIntegerField(default=0)
    total_interest = models.BigIntegerField(default=0)

    class Meta:
        verbose_name_plural = "Savings Interests"
        ordering = ["-created_at", "member__name", "-total_interest"]

    def __str__(self):
        return "SI({}, {}, {}, {}, {}, {})".format(
            self.member.name,
            self.savings.__str__(),
            self.amount_display,
            self.interest_display,
            self.total_interest_display,
            format_date_model(self.created_at),
        )

    @property
    def interest_display(self):
        return get_amount(self.interest)

    @property
    def total_interest_display(self):
        return get_amount(self.total_interest)


class SavingsInterestTotal(Savings):
    savings = models.OneToOneField(SavingsCredit, on_delete=models.CASCADE)
    interest = models.BigIntegerField(default=0)
    is_comp = models.BooleanField("Is Compounding?", default=True)
    start_comp = models.BooleanField("Started Compounding?", default=False)
    disabled = models.BooleanField(default=False)
    updated_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["member__name", "-created_at"]
        verbose_name_plural = "Savings Interests Total"

    def __str__(self):
        return "SIT({}, {}, {}, {}, is: {}, sc: {}, dis: {}, {}, {})".format(
            self.member.name,
            self.savings.__str__(),
            self.amount_display,
            self.interest_display,
            self.is_comp,
            self.start_comp,
            self.disabled,
            format_date_model(self.created_at),
            format_date_model(self.updated_at),
        )

    @property
    def interest_display(self):
        return get_amount(self.interest)


@receiver(post_save, sender=SavingsCredit)
def post_savings_credit_save(sender, instance: SavingsCredit, **kwargs):
    si = SavingsInterestTotal.objects.get_or_create(
        savings=instance, member=instance.member
    )[0]
    si.amount = instance.amount
    # si.updated_at = instance.created_at
    si.created_at = instance.created_at
    si.updated_at = timezone.now()
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


@receiver(post_save, sender=SavingsInterestTotal)
def post_savings_interest_total_save(sender, instance: SavingsInterestTotal, **kwargs):
    update_savings_total(member=instance.member)


@receiver(post_save, sender=SavingsDebit)
def post_savings_debit_save(sender, instance: SavingsDebit, **kwargs):
    if kwargs["created"]:
        handle_withdrawal(context="create", instance=instance)


# @receiver(post_delete, sender=SavingsCredit)
def post_savings_credit_delete(sender, instance: SavingsCredit, **kwargs):
    if instance.reason == "credit-eoy":
        YearEndBalance.objects.filter(
            member=instance.member,
            amount=instance.amount,
            created_at=instance.created_at,
        ).delete()


# @receiver(post_delete, sender=SavingsDebit)
def post_savings_debit_delete(sender, instance: SavingsDebit, **kwargs):
    handle_withdrawal(context="delete", instance=instance)


# @receiver(post_delete, sender=SavingsInterestTotal)
def post_savings_interest_total_delete(
    sender, instance: SavingsInterestTotal, **kwargs
):
    update_savings_total(member=instance.member)
