import phonenumbers
from django import forms
from email_validator import EmailNotValidError, validate_email
from phonenumbers.phonenumberutil import NumberParseException

from accounts.models import Member
from cedar.mixins import get_member_choices


class ServiceForm(forms.ModelForm):
    amount = forms.FloatField(
        required=True, widget=forms.NumberInput(attrs={"min": 0, "step": 0.01})
    )

    def __init__(self, *args, **kwargs):
        super(ServiceForm, self).__init__(*args, **kwargs)
        self.fields["member"].widget = forms.Select()
        self.fields["member"].choices = get_member_choices()

    def clean(self):
        data = self.cleaned_data
        data["amount"] = _validate_amount(amount=data.get("amount"))
        return data


def _validate_email(email: str, ignore_empty=False, **kwargs):
    email = _validate_empty(data=email, kwargs=kwargs)
    if email != "":
        try:
            is_valid = validate_email(email=email)
        except EmailNotValidError:
            raise forms.ValidationError(
                "Invalid" if not "field" in kwargs else {kwargs["field"]: "Invalid"}
            )
        else:
            email = is_valid.ascii_email
            if kwargs and "check_exist" in kwargs:
                is_exist = Member.objects.filter(email=email).exists()
                if is_exist:
                    raise forms.ValidationError(
                        "Already used"
                        if not "field" in kwargs
                        else {kwargs["field"]: "Already used"}
                    )
    return email


def _validate_phone(phone: str, ignore_empty=False, **kwargs):
    phone = _validate_empty(data=phone, ignore_empty=ignore_empty, kwargs=kwargs)
    raise_error = lambda message: forms.ValidationError(
        message if not "field" in kwargs else {kwargs["field"]: message}
    )
    if phone != "":
        try:
            number = phonenumbers.parse(str(phone), "NG")
        except NumberParseException:
            message = "Invalid phone number"
            raise raise_error(message=message)
        else:
            is_valid = phonenumbers.is_possible_number(number)
            if is_valid:
                phone = phonenumbers.format_number(
                    number, phonenumbers.PhoneNumberFormat.INTERNATIONAL
                )
            else:
                message = "Invalid phone number"
                raise raise_error(message=message)

            phone = "".join(phone.replace("-", "").split())
            if kwargs and "check_exist" in kwargs:
                is_exist = Member.objects.filter(phone=phone).exists()
                if is_exist:
                    message = "Already used"
                    raise raise_error(message=message)
    return phone


def _validate_empty(data: str, ignore_empty=False, **kwargs):
    if ignore_empty:
        data = data if data != "" or data is not None else ""
    else:
        if data == "" or data is None:
            raise forms.ValidationError(
                "This field is required"
                if not "field" in kwargs
                else {kwargs["field"]: "This field is required"}
            )
    return data


def _validate_name(name: str, **kwargs):
    name = _validate_empty(data=name, kwargs=kwargs)
    return " ".join([item.capitalize() for item in name.split()])


def _validate_amount(amount, **kwargs):
    amount = str(amount)
    if amount.count("e") > 0:
        raise forms.ValidationError(
            "Input a number"
            if not "field" in kwargs
            else {kwargs["field"]: "Input a number"}
        )

    return int(float(amount) * 100)
