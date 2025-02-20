from import_export import resources

from savings.models import SavingsCredit, SavingsDebit


class BaseSavingsResource(resources.ModelResource):
    def dehydrate_member(self, instance):
        return instance.member.name.upper()

    class Meta:
        fields = ("id", "member", "amount", "reason", "created_at")
        export_order = fields


class SavingsCreditResource(BaseSavingsResource):
    class Meta(BaseSavingsResource.Meta):
        model = SavingsCredit


class SavingsDebitResource(BaseSavingsResource):
    class Meta(BaseSavingsResource.Meta):
        model = SavingsDebit
