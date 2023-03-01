from django.db import models
from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch.dispatcher import receiver

from accounts.models import Member
from cedar.mixins import CustomAbstractTable, get_amount, format_date_model
from shares.mixins import update_shares_total
from django.utils import timezone


# Create your models here.
class Shares(models.Model):
    member = models.ForeignKey(Member, on_delete=models.CASCADE)
    amount = models.BigIntegerField()
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name_plural = "Shares"

    def __str__(self):
        return "({}, {}, {})".format(
            self.member.name,
            get_amount(self.amount),
            format_date_model(self.created_at),
        )


class SharesTotal(CustomAbstractTable):
    member = models.OneToOneField(Member, on_delete=models.CASCADE)

    class Meta:
        verbose_name_plural = "Shares Total"

    def __str__(self):
        return "({}, {}, {},{})".format(
            self.member.name,
            get_amount(self.amount),
            format_date_model(self.created_at),
            format_date_model(self.updated_at),
        )


@receiver(post_save, sender=Shares)
def post_shares_save(sender, instance: Shares, **kwargs):
    update_shares_total(instance.member, instance.created_at)


@receiver(post_delete, sender=Shares)
def post_shares_delete(sender, instance: Shares, **kwargs):
    update_shares_total(instance.member, instance.created_at)
