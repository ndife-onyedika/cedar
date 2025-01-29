from django.contrib import admin

from cedar.admin import CustomAdmin
from utils.helpers import display_duration, display_rate

from .models import AccountChoice, BusinessYear


# Register your models here.
@admin.register(AccountChoice)
class AccountChoiceAdmin(CustomAdmin):
    list_display = (
        "name",
        "view_lir",
        "view_sir",
        "view_lsr",
        "view_ld",
        "view_psisd",
        "view_aad",
    )
    # "country",
    list_display_links = ("name",)
    readonly_fields = ("created_at",)

    search_fields = ("name",)
    ordering = ("name",)

    def view_lir(self, obj):
        return display_rate(obj.lir)

    view_lir.short_description = "Loan Interest Rate"

    def view_sir(self, obj):
        return display_rate(obj.sir)

    view_sir.short_description = "Savings Interest Rate"

    def view_lsr(self, obj):
        return display_rate(obj.lsr)

    view_lsr.short_description = "Loan Savings Rate"

    def view_ld(self, obj):
        return display_duration(obj.ld)

    view_ld.short_description = "Loan Duration"

    def view_psisd(self, obj):
        return display_duration(obj.psisd)

    view_psisd.short_description = "Pre-Savings Interest Start Duration"

    def view_aad(self, obj):
        return display_duration(obj.aad)

    view_aad.short_description = "Account Activity Duration Duration"


@admin.register(BusinessYear)
class BusinessYearAdmin(CustomAdmin):
    list_display = ("start_day", "start_month", "end_day", "end_month")
    ordering = ("-id",)
