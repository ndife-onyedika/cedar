from django.db import models
from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch.dispatcher import receiver

from accounts.models import Member
from cedar.mixins import CustomAbstractTable
from shares.mixins import update_shares_total


# Create your models here.
class Shares(models.Model):
    member = models.ForeignKey(Member, on_delete=models.CASCADE)
    amount = models.BigIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)


class SharesTotal(CustomAbstractTable):
    member = models.OneToOneField(Member, on_delete=models.CASCADE)


@receiver(post_save, sender=Shares)
def post_shares_save(sender, instance: Shares, **kwargs):
    update_shares_total(instance.member, instance.created_at)


@receiver(post_delete, sender=Shares)
def post_shares_delete(sender, instance: Shares, **kwargs):
    update_shares_total(instance.member, instance.created_at)
