from django import forms
from cedar.constants import MONTH_CHOICES

from settings.models import AccountChoice, BusinessYear


AccountChoiceFormSet = forms.modelformset_factory(
    AccountChoice,
    max_num=2,
    exclude=("created_at", "id"),
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
