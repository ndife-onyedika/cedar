from django import forms

from settings.models import AccountChoice, BusinessYear


AccountChoiceFormSet = forms.modelformset_factory(
    AccountChoice, max_num=2, edit_only=True, exclude=("created_at",)
)


class BusinessYearForm(forms.ModelForm):
    class Meta:
        model = BusinessYear
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super(BusinessYearForm, self).__init__(*args, **kwargs)
        self.fields["start_month"].widget = forms.ChoiceWidget
        self.fields["end_month"].widget = forms.ChoiceWidget
