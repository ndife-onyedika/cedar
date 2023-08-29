from django.urls import path

from .views import (
    data_table,
    get_chart,
    get_loan,
    perform_action,
    notify_list,
    notify_delete,
    notify_mark_read,
    notify_unread_count,
    service_create,
    update_settings,
)

app_name = "ajax"
urlpatterns = [
    path("pa", perform_action, name="pa"),
    path("gc", get_chart, name="gc"),
    path("dt", data_table, name="dt"),
    path("us", update_settings, name="us"),
    path("sc/<str:context>", service_create, name="sc"),
    path("gld/<int:member_id>", get_loan, name="gld"),
    path("notify/list", notify_list, name="notify.list"),
    path("notify/unread_count", notify_unread_count, name="notify.unread_count"),
    path("notify/mark_read", notify_mark_read, name="notify.mark_read"),
    path("notify/delete", notify_delete, name="notify.delete"),
]
