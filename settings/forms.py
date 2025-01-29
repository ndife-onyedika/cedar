from django import forms
from django.utils import timezone

from dashboard.forms import _validate_empty
from settings.models import AccountChoice, BusinessYear
from utils.choices import MONTH_CHOICES
from utils.helpers import check_day_valid

AccountChoiceFormSet = forms.modelformset_factory(
    AccountChoice,
    max_num=2,
    exclude=("created_at", "id"),
    widgets={
        "name": forms.TextInput(
            attrs={
                "readonly": True,
                "required": False,
                "class": "form-control-plaintext bg-light",
            }
        ),
    },
)


class BusinessYearForm(forms.ModelForm):
    class Meta:
        model = BusinessYear
        exclude = ("id",)

    def __init__(self, *args, **kwargs):
        super(BusinessYearForm, self).__init__(*args, **kwargs)
        self.fields["start_month"].widget = forms.Select()
        self.fields["start_month"].choices = MONTH_CHOICES
        self.fields["end_month"].widget = forms.Select()
        self.fields["end_month"].choices = MONTH_CHOICES

    def clean(self):
        data = self.cleaned_data
        sd = data["start_day"] = int(
            _validate_empty(data=data.get("start_day"), field=data["start_day"])
        )
        sm = data["start_month"] = int(data.get("start_month"))
        ed = data["end_day"] = int(
            _validate_empty(data=data.get("end_day"), field=data["end_day"])
        )
        em = data["end_month"] = int(data.get("end_month"))
        if sm != 2:
            is_valid = check_day_valid(sd, sm, timezone.now().year)
            if not is_valid:
                raise forms.ValidationError(
                    {"start_day": "Day is not valid for said month."}
                )
        else:
            if sd > 28:
                raise forms.ValidationError(
                    {"start_day": "Day should be from 1-28 for the month of February"}
                )

        if em != 2:
            is_valid = check_day_valid(ed, em, timezone.now().year)
            if not is_valid:
                raise forms.ValidationError(
                    {"end_day": "Day is not valid for said month."}
                )
        else:
            if ed > 28:
                raise forms.ValidationError(
                    {"end_day": "Day should be from 1-28 for the month of February"}
                )

        return data

    def save(self):
        data = self.cleaned_data
        self.instance.start_day = data.get("start_day", self.instance.start_day)
        self.instance.start_month = data.get("start_month", self.instance.start_month)
        self.instance.end_day = data.get("end_day", self.instance.end_day)
        self.instance.start_month = data.get("start_month", self.instance.start_month)
        self.instance.save()
