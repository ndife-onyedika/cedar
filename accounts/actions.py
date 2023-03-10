from django.db import IntegrityError, transaction


def set_nok(modeladmin, request, queryset):
    from .models import NextOfKin
    from savings.models import SavingsInterest

    for instance in queryset:
        try:
            with transaction.atomic():
                si = SavingsInterest.objects.filter(member=instance)
                if len(si) > 0:
                    si = si[0]
                    si.save()
                # NextOfKin.objects.get_or_create(member=instance)
        except IntegrityError as e:
            raise Exception(f"ACCOUNTNEXTOFKINACTION: {e}")
