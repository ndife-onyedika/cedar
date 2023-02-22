from django import forms
from django.conf import settings as dj_sett
from django.contrib.auth import authenticate
from django.contrib.auth.forms import (
    AuthenticationForm,
    PasswordResetForm,
    SetPasswordForm,
)
from django.contrib.sites.models import Site
from django.template.loader import get_template
from django.utils.http import urlsafe_base64_encode
from django.utils.translation import ugettext as _

from cedar.constants import RELATIONSHIP_CHOICE
from cedar.mixins import TokenGenerator, get_account_choices, send_mass_html_mail
from dashboard.forms import (
    _validate_email,
    _validate_empty,
    _validate_name,
    _validate_phone,
)
from settings.models import AccountChoice

from .models import Member, NextOfKin, User


class MemberForm(forms.ModelForm):
    nok_name = forms.CharField(label="Name", required=False)
    nok_email = forms.EmailField(label="Email address", required=False)
    nok_phone = forms.CharField(label="Phone number", required=False)
    nok_address = forms.CharField(
        label="Address", required=False, widget=forms.Textarea
    )
    nok_relationship = forms.ChoiceField(
        required=False,
        label="Relationship",
        choices=[(None, "Select Relationship")] + RELATIONSHIP_CHOICE,
    )

    class Meta:
        model = Member
        exclude = ["is_active", "date_joined"]

    def validate(self, data):
        data["address"] = _validate_empty(
            data=data.get("address"), field="address", ignore_empty=True
        )
        data["occupation"] = _validate_empty(
            data=data.get("occupation"), field="occupation", ignore_empty=True
        )
        data["nok_name"] = _validate_name(
            name=data.get("nok_name"), field="nok_name", ignore_empty=True
        )
        data["nok_email"] = _validate_email(
            email=data.get("nok_email"), field="nok_email", ignore_empty=True
        )
        data["nok_phone"] = _validate_phone(
            phone=data.get("nok_phone"), field="nok_phone", ignore_empty=True
        )
        data["nok_address"] = _validate_empty(
            data=data.get("nok_address"), field="nok_address", ignore_empty=True
        )
        data["nok_relationship"] = _validate_empty(
            data=data.get("nok_relationship"), field="nok_relationship"
        )
        return data


class RegistrationForm(MemberForm):
    def __init__(self, *args, **kwargs):
        super(MemberForm, self).__init__(*args, **kwargs)
        self.fields["account_type"].widget = forms.RadioSelect()
        self.fields["account_type"].choices = get_account_choices(form=False)

    def clean(self):
        data = self.cleaned_data
        name = data["name"] = _validate_name(name=data.get("name"), field="name")
        phone = data["phone"] = _validate_phone(
            phone=data.get("phone"), field="phone", check_exist=True, ignore_empty=True
        )
        email = data["email"] = _validate_email(
            email=data.get("email"), field="email", check_exist=True, ignore_empty=True
        )

        data = self.validate(data)

        if name != "" and data["nok_name"] != "" and name == data["nok_name"]:
            raise forms.ValidationError(
                {"nok_name": "Identical name used for registration"}
            )
        if email != "" and data["nok_email"] != "" and email == data["nok_email"]:
            raise forms.ValidationError(
                {"nok_email": "Identical email used for registration"}
            )
        if phone != "" and data["nok_phone"] != "" and phone == data["nok_phone"]:
            raise forms.ValidationError(
                {"nok_phone": "Identical phone number used for registration"}
            )
        return data

    def save(self):
        data = self.cleaned_data
        member = Member.objects.create(
            name=data.get("name"),
            phone=data.get("phone"),
            email=data.get("email"),
            avatar=data.get("avatar"),
            address=data.get("address"),
            occupation=data.get("occupation"),
            account_type=data.get("account_type"),
            account_number=data.get("account_number"),
        )
        NextOfKin.objects.create(
            member=member,
            name=data.get("nok_name"),
            phone=data.get("nok_phone"),
            email=data.get("nok_email"),
            address=data.get("nok_address"),
            relationship=data.get("nok_relationship"),
        )
        return member


class EditMemberForm(MemberForm):
    def __init__(self, *args, **kwargs):
        updated_initial = {}
        self.member = kwargs.get("instance")
        updated_initial["nok_name"] = self.member.nextofkin.name
        updated_initial["nok_email"] = self.member.nextofkin.email
        updated_initial["nok_phone"] = self.member.nextofkin.get_phone
        updated_initial["nok_address"] = self.member.nextofkin.address
        updated_initial["nok_relationship"] = self.member.nextofkin.relationship

        # Finally update the kwargs initial reference
        kwargs.update(initial=updated_initial)
        super(EditMemberForm, self).__init__(*args, **kwargs)
        del self.fields["account_type"]

    def clean(self):
        data = self.cleaned_data
        name = data["name"] = _validate_name(name=data.get("name"), field="name")
        phone = data["phone"] = _validate_phone(
            phone=data.get("phone"), field="phone", ignore_empty=True
        )
        email = data["email"] = _validate_email(
            email=data.get("email"), field="email", ignore_empty=True
        )

        excluded_member = Member.objects.exclude(id=self.member.id)
        if email != "":
            email_exists = excluded_member.filter(phone=phone).exists()
            if email_exists:
                raise forms.ValidationError(
                    {"email": "Email address used by another member"}
                )

        if phone != "":
            phone_exists = excluded_member.filter(phone=phone).exists()
            if phone_exists:
                raise forms.ValidationError(
                    {"phone": "Phone number used by another member"}
                )

        data = self.validate(data)
        if "" not in (name, data["nok_name"]) and name == data["nok_name"]:
            raise forms.ValidationError({"nok_name": "Identical name with member"})
        if "" not in (email, data["nok_email"]) and email == data["nok_email"]:
            raise forms.ValidationError({"nok_email": "Identical email with member"})
        if "" not in (phone, data["nok_phone"]) and phone == data["nok_phone"]:
            raise forms.ValidationError(
                {"nok_phone": "Identical phone number with member"}
            )
        return data

    def save(self):
        data = self.cleaned_data
        instance = self.instance
        print(instance)
        instance.name = data.get("name", instance.name)
        instance.email = data.get("email", instance.email)
        instance.phone = data.get("phone", instance.phone)
        instance.address = data.get("address", instance.address)
        instance.occupation = data.get("occupation", instance.occupation)
        instance.nextofkin.name = data.get("nok_name", instance.nextofkin.name)
        instance.nextofkin.email = data.get("nok_email", instance.nextofkin.email)
        instance.nextofkin.phone = data.get("nok_phone", instance.nextofkin.phone)
        instance.nextofkin.address = data.get("nok_address", instance.nextofkin.address)
        instance.nextofkin.relationship = data.get(
            "nok_relationship", instance.nextofkin.relationship
        )
        instance.save()
        instance.nextofkin.save()
        return instance


class LoginForm(AuthenticationForm):
    email = forms.EmailField(required=True)

    error_messages = {
        "invalid_login": _(
            "Please enter a correct email and password. Note that both "
            "fields may be case-sensitive."
        ),
        "inactive": _("This account is inactive."),
    }

    def __init__(self, *args, **kwargs):
        super(LoginForm, self).__init__(*args, **kwargs)
        del self.fields["username"]

    def clean(self):
        email = self.cleaned_data.get("email")
        password = self.cleaned_data.get("password")

        if email is not None and password:
            self.user_cache = authenticate(self.request, email=email, password=password)
            if self.user_cache is None:
                raise self.get_invalid_login_error()
            else:
                self.confirm_login_allowed(self.user_cache)

        return self.cleaned_data

    def get_invalid_login_error(self):
        return forms.ValidationError(
            self.error_messages["invalid_login"],
            code="invalid_login",
        )


class CustomPasswordResetForm(PasswordResetForm):
    def __init__(self, *args, **kwargs):
        super(CustomPasswordResetForm, self).__init__(*args, **kwargs)
        self.fields["email"].max_length = None

    def get_user(self, email):
        """Given an email, return matching user(s) who should receive a reset.

        This allows subclasses to more easily customize the default policies
        that prevent inactive users and users with unusable passwords from
        resetting their password.
        """
        _user = User.objects.filter(email=email).first()
        if (
            hasattr(_user, "member")
            and _user.member.is_verified
            and _user.is_active
            or hasattr(_user, "executive")
            and _user.is_active
        ):
            return _user
        else:
            return None

    def save(
        self,
        domain_override=None,
        use_https=dj_sett.DEBUG,
        token_generator=TokenGenerator(),
        subject_template_name="registration/password_reset_subject.txt",
        email_template_name="registration/password_reset_email.html",
    ):
        """
        Generate a one-use only link for resetting password and send it to the
        user.
        """
        email = self.cleaned_data["email"]
        user = self.get_user(email)
        if not user is None:
            if not domain_override:
                current_site = Site.objects.get_current()
                site_name = current_site.name
                domain = current_site.domain
            else:
                site_name = domain = domain_override
            data = {
                "user": user,
                "email": email,
                "domain": domain,
                "site_name": site_name,
                "token": token_generator.make_token(
                    email=email, uid=urlsafe_base64_encode(str(user.pk).encode())
                ),
                "protocol": "https" if use_https else "http",
            }
            subject = open(get_template(subject_template_name).origin.name, "r").read()
            html_body = get_template(email_template_name).render(data)

            message = (
                subject,
                html_body,
                None,
                [email],
                None,
                [dj_sett.MAIL_DEV] if not use_https else None,
                None,
            )
            try:
                send_mass_html_mail(datalist=[message], context="single")
            except Exception:
                return False
            else:
                return True


class CustomSetPasswordForm(SetPasswordForm):
    def save(self, commit=True):
        password = self.cleaned_data["new_password1"]
        self.user.set_password(password)
        self.user.is_active = True
        if commit:
            self.user.save()
        return self.user
