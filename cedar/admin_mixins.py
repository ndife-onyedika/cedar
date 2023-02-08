from django.contrib import messages
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.mixins import AccessMixin
from accounts.models import Member


class InternalModelAdminMixin:
    """Mixin to catch all errors in the Django Admin and map them to user-visible errors."""

    def add_view(self, request, form_url="", extra_context=None):
        try:
            return super().add_view(request, form_url, extra_context)
        except Exception as e:
            self.message_user(
                request=request,
                message=f"Error: {e}",
                level=messages.ERROR,
            )
            # This logic was cribbed from the `add_view()` handling here:
            # django/contrib/admin/options.py:response_post_save_add()
            # There might be a simpler way to do this, but it seems to do the job.
            return HttpResponseRedirect(request.path)

    def change_view(self, request, object_id, form_url="", extra_context=None):
        try:
            return super().change_view(request, object_id, form_url, extra_context)
        except Exception as e:
            self.message_user(
                request=request,
                message=f"Error: {e}",
                level=messages.ERROR,
            )
            # This logic was cribbed from the `change_view()` handling here:
            # django/contrib/admin/options.py:response_post_save_add()
            # There might be a simpler way to do this, but it seems to do the job.
            return HttpResponseRedirect(request.path)

    def changelist_view(self, request, extra_context=None):
        try:
            return super().changelist_view(request, extra_context)
        except Exception as e:
            self.message_user(
                request=request,
                message=f"Error: {e}",
                level=messages.ERROR,
            )
            # This logic was cribbed from the `changelist_view()` handling here:
            # django/contrib/admin/options.py:response_post_save_add()
            # There might be a simpler way to do this, but it seems to do the job.
            return HttpResponseRedirect(request.path)


class CustomLoginRequiredMixin(AccessMixin):
    """Verify that the current user is authenticated."""

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return self.allow_valid_member_or_httpresponse(request, *args, **kwargs)
        else:
            return self.handle_no_permission()

    def allow_valid_member_or_httpresponse(self, request, *args, **kwargs):
        if hasattr(request.user, "executive"):
            return HttpResponse("<h1>Dashboard unavailable for Admin Accounts</h1>")
        return super().dispatch(request, *args, **kwargs)
