from datetime import time

import phonenumbers
from django import forms
from django.utils.timezone import datetime, make_aware, now
from email_validator import EmailNotValidError, validate_email
from phonenumbers.phonenumberutil import NumberParseException

from accounts.models import Member, User


class ServiceForm(forms.ModelForm):
    amount = forms.FloatField(widget=forms.NumberInput(attrs={"min": 0, "step": 0.01}))

    class Meta:
        fields = ["member", "created_at"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        initial = kwargs.get("initial", {})
        self.fields["member"].choices = [
            (None, "Choose one"),
            *[*self.fields["member"].choices][1:],
        ]
        if initial and initial.get("member"):
            self.fields["member"].disabled = True
            self.fields["member"].initial = initial["member"]
            self.fields["member"].widget.attrs = {"readonly": True}

        if self.fields.get("created_at"):
            self.fields["created_at"].initial = None
            self.fields["created_at"].label = "Date"

    def clean(self):
        data = self.cleaned_data
        data["amount"] = _validate_amount(
            form=self, field="amount", amount=data.get("amount")
        )
        if created_at := data.get("created_at"):
            data["created_at"] = (
                now()
                if created_at.date() == now().date()
                else make_aware(datetime.combine(created_at.date(), time(2, 0)))
            )
        return data


def _validate_email(form, field: str, email: str, check_exist=False):
    email = _validate_empty(form, field, email)
    try:
        is_valid = validate_email(email=email)
    except EmailNotValidError:
        form.add_error(field, "Invalid email address")
    else:
        email = is_valid.ascii_email
        if check_exist:
            is_exist = User.objects.filter(email=email).exists()
            if is_exist:
                form.add_error(field, "Email address already used")
    return email.lower()


def _validate_phone(form, field: str, phone: str, check_exist=False):
    phone = _validate_empty(form, field, phone)
    add_error = lambda message: form.add_error(field, message)

    try:
        number = phonenumbers.parse(phone, "NG")
    except NumberParseException:
        add_error(message="Invalid phone number")
    else:
        is_valid = phonenumbers.is_possible_number(number)
        if is_valid:
            phone = phonenumbers.format_number(
                number, phonenumbers.PhoneNumberFormat.INTERNATIONAL
            )
        else:
            add_error(message="Invalid phone number")

        phone = "".join(phone.replace("-", "").split())
        if len(phone) != 14:
            add_error(message="Invalid phone number")

        if check_exist:
            is_exist = Member.objects.filter(phone=phone).exists()
            if is_exist:
                add_error(message="Phone number already used")
    return phone


def _validate_empty(form, field: str, data: str):
    if not data:
        form.add_error(field, "This field is required")
    return data


def _validate_name(form, field: str, name: str):
    name = _validate_empty(form, field, name)
    name = name.split()
    return " ".join([item.capitalize() for item in name])


def _validate_amount(form, field: str, amount):
    amount = _validate_empty(form, field, amount)
    if str(amount).count(".") > 0:
        amount = str(amount).split(".")
        if len(amount[1]) > 2:
            form.add_error(field, "Check amount")
        amount = ".".join(amount)
    elif str(amount).count("e") > 0:
        form.add_error(field, "Check amount")
    return None if not amount else int(float(amount) * 100)
