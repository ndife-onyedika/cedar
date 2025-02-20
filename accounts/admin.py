from django.contrib import admin
from django.contrib.admin.models import LogEntry

from accounts.forms import UserChangeForm, UserCreationForm
from accounts.models import Member, User
from accounts.utils.actions import run_task, set_nok
from accounts.utils.resources import MemberResource
from cedar.admin import CustomAdmin, CustomImportExportAdmin


# Register your models here.
@admin.register(LogEntry)
class LogEntryAdmin(admin.ModelAdmin):
    # to have a date-based drilldown navigation in the admin page
    date_hierarchy = "action_time"
    # to filter the results by users, content types and action flags
    list_filter = ["user", "content_type", "action_flag"]
    # when searching the user will be able to search in both object_repr and change_message
    search_fields = ["object_repr", "change_message"]
    list_display = ["action_time", "user", "content_type", "action_flag"]


@admin.register(User)
class UserAdmin(CustomAdmin):
    add_form = UserCreationForm
    form = UserChangeForm

    ordering = ("name",)
    list_display_links = ("name",)
    search_fields = ("name", "email")
    readonly_fields = ("date_joined",)
    list_display = ("name", "email", "is_superuser")
    fieldsets = (
        ("Account Info", {"fields": ("email", "password")}),
        ("Personal Info", {"fields": ("name",)}),
        (
            "Permissions",
            {
                "classes": ("collapse",),
                "fields": ("is_active", "is_staff", "is_superuser", "groups"),
            },
        ),
        (
            "Important dates",
            {"classes": ("collapse",), "fields": ("last_login", "date_joined")},
        ),
    )


@admin.register(Member)
class MemberAdmin(CustomImportExportAdmin, CustomAdmin):
    # actions = [set_nok, run_task]
    resource_class = MemberResource

    date_hierarchy = "date_joined"

    list_display = (
        "name",
        "account_number",
        "account_type",
        "email",
        "phone",
        "is_active",
        "date_joined",
    )
    ordering = ("name",)
    search_fields = ("name", "email")
    list_filter = ("is_active", "account_type")
    fieldsets = (
        ("Account Info", {"fields": ("account_type", "account_number")}),
        (
            "Personal Info",
            {"fields": ("avatar", "name", "email", "phone", "occupation", "address")},
        ),
        ("Permissions", {"classes": ("collapse",), "fields": ("is_active",)}),
    )
