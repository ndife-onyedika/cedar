import notifications.urls
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path

from accounts.views import _logout, login_view, password_reset_request
from cedar.views import index

admin.site.site_header = "9Mile Administration"
admin.site.site_title = "9Mile"
admin.site.empty_value_display = "-empty-"

urlpatterns = [
    path("", index, name="home"),
    path("admin/", admin.site.urls),
    path("login/", login_view, name="sign_in"),
    path("logout/", _logout, name="sign_out"),
    path("dashboard/", include("dashboard.urls")),
    path("ajax/", include("ajax.urls")),
    path(
        "inbox/notifications/", include(notifications.urls, namespace="notifications")
    ),
    # PASSWORD RESET START
    path(
        "password_reset/",
        password_reset_request,
        name="password_reset",
    ),
    path(
        "password_reset/done/",
        auth_views.PasswordResetDoneView.as_view(
            template_name="registration/password_reset_done.html"
        ),
        name="password_reset_done",
    ),
    path(
        "reset/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            template_name="registration/password_reset_confirm.html"
        ),
        name="password_reset_confirm",
    ),
    path(
        "reset/done/",
        auth_views.PasswordResetCompleteView.as_view(
            template_name="registration/password_reset_complete.html"
        ),
        name="password_reset_complete",
    ),
    # PASSWORD RESET END
]
if settings.DEBUG:
    urlpatterns += [path("api/", include("api.urls"))]
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
