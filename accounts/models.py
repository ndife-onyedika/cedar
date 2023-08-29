from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import IntegrityError, models, transaction
from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch.dispatcher import receiver
from django.utils import timezone
from django_fields import DefaultStaticImageField
from phonenumber_field.modelfields import PhoneNumberField

from accounts.manager import UserManager
from cedar.constants import RELATIONSHIP_CHOICE
from cedar.mixins import create_tables
from settings.models import AccountChoice


# Create your models here.
class User(AbstractBaseUser, PermissionsMixin):
    name = models.CharField(max_length=250)
    email = models.EmailField("Email", unique=True)

    is_active = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)

    EMAIL_FIELD = "email"
    USERNAME_FIELD = "email"

    objects = UserManager()

    class Meta:
        """More info."""

        db_table = "users"
        verbose_name = "Admin"
        verbose_name_plural = "Admins"

    def get_absolute_url(self):
        return "/accounts/{}".format(self.pk)

    def __str__(self):
        return "{} ({})".format(self.name, self.email)


class Member(models.Model):
    name = models.CharField(max_length=250)
    email = models.EmailField("Email address", null=True, blank=True)
    phone = PhoneNumberField("Phone number", null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    occupation = models.CharField(max_length=50, null=True, blank=True)
    avatar = DefaultStaticImageField(
        blank=True,
        upload_to="avatars/",
        default_image_path="/img/avatar/default_avatar.png",
    )
    account_number = models.CharField(max_length=50)
    account_type = models.ForeignKey(AccountChoice, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return "{} ({})".format(self.name, "Active" if self.is_active else "Inactive")

    @property
    def get_phone(self) -> str:
        """The Member's Phone"""
        return self.phone.as_e164 if self.phone else ""


class NextOfKin(models.Model):
    member = models.OneToOneField(Member, on_delete=models.CASCADE)
    name = models.CharField(max_length=250, null=True, blank=True)
    email = models.EmailField("Email address", null=True, blank=True)
    phone = PhoneNumberField("Phone number", null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    relationship = models.CharField(
        "Relationship with Kin",
        null=True,
        blank=True,
        max_length=100,
        choices=RELATIONSHIP_CHOICE,
    )

    class Meta:
        verbose_name = "Next Of Kin"
        verbose_name_plural = "Next Of Kins"

    @property
    def get_phone(self):
        """The Next of KIn's Phone"""
        return self.phone.as_e164 if self.phone else ""


@receiver(post_save, sender=Member)
def post_member_save(sender, instance, **kwargs):
    if kwargs["created"]:
        create_tables(instance)
