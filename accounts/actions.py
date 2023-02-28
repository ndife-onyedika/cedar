from django.db import IntegrityError, transaction


def set_nok(modeladmin, request, queryset):
    from .models import NextOfKin

    for instance in queryset:
        try:
            with transaction.atomic():
                NextOfKin.objects.get_or_create(member=instance)
        except IntegrityError as e:
            raise Exception(f"ACCOUNTNEXTOFKINACTION: {e}")
