from django.contrib import admin
from cedar.mixins import get_amount

from shares.models import Shares, SharesTotal
from cedar.admin import CustomAdmin


# Register your models here.
@admin.register(Shares)
class SharesAdmin(CustomAdmin):
    list_display = ("member", "view_amount", "created_at")
    list_display_links = ("member",)

    search_fields = ("member__name", "member__email")
    ordering = ("-created_at",)
    list_filter = ("created_at",)
    autocomplete_fields = ["member"]

    def view_amount(self, obj):
        return get_amount(obj.amount)

    view_amount.short_description = "Amount"


@admin.register(SharesTotal)
class SharesTotalAdmin(CustomAdmin):
    list_display = ("member", "view_amount", "created_at", "updated_at")
    list_display_links = ("member",)

    search_fields = ("member__name", "member__email")
    ordering = ("member__name",)
    list_filter = ("created_at", "updated_at")
    autocomplete_fields = ["member"]

    def view_amount(self, obj):
        return get_amount(obj.amount)

    view_amount.short_description = "Amount"
