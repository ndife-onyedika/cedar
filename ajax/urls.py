from django.urls import path

from .views import (
    data_table,
    get_chart,
    get_loan,
    service_delete,
    notify_list,
    notify_delete,
    notify_mark_read,
    notify_unread_count,
    service_create,
    service_export,
    service_fetch,
    service_update,
    update_settings,
)

app_name = "ajax"
urlpatterns = [
    path("gc", get_chart, name="gc"),
    path("dt", data_table, name="dt"),
    path("us", update_settings, name="us"),
    path("sc/<str:context>", service_create, name="sc"),
    path("sd/<str:context>", service_delete, name="sd"),
    path("se/<str:context>", service_export, name="se"),
    path("sf/<str:context>/<int:id>", service_fetch, name="sf"),
    path("su/<str:context>/<int:id>", service_update, name="su"),
    path("gld/<int:member_id>", get_loan, name="gld"),
    path("notify/list", notify_list, name="notify.list"),
    path("notify/unread_count", notify_unread_count, name="notify.unread_count"),
    path("notify/mark_read", notify_mark_read, name="notify.mark_read"),
    path("notify/delete", notify_delete, name="notify.delete"),
]
