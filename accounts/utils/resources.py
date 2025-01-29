from import_export import resources

from accounts.models import Member


class MemberResource(resources.ModelResource):
    def dehydrate_member(self, instance):
        return instance.member.name.upper()

    class Meta:
        model = Member
        fields = (
            "id",
            "name",
            "account_number",
            "account_type",
            "email",
            "phone",
            "date_joined",
        )
        export_order = fields
