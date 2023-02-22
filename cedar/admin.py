from django.contrib import admin
from django.contrib.auth.models import Permission

from .admin_mixins import InternalModelAdminMixin

admin.site.register(Permission)


class CustomAdmin(InternalModelAdminMixin, admin.ModelAdmin):
    list_per_page = 20
