def update_shares_total(member, date):
    from .models import Shares, SharesTotal

    shares = Shares.objects.filter(member=member)
    total_amount = 0
    if shares.count() > 0:
        for share in shares:
            total_amount += share.amount
        shares_total = SharesTotal.objects.get_or_create(member=member)[0]
        shares_total.amount = total_amount
        shares_total.updated_at = date
        shares_total.save()
