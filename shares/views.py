from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, render
from django.views.generic import TemplateView

from accounts.models import Member


# Create your views here.
class ShareListView(LoginRequiredMixin, TemplateView):
    def get(self, request, *args, **kwargs):
        context = {
            "dashboard": {
                "context": "shares",
                "title": "Shares",
                "buttons": [
                    {
                        "target": "#asm",
                        "title": "Add Share",
                        "class": "btn-primary",
                    },
                ],
            }
        }
        template = f"dashboard/records/index.html"
        return render(request, template, context)


class MemberSharesListView(LoginRequiredMixin, TemplateView):
    def get(self, request, member_id: int, *args, **kwargs):
        member = get_object_or_404(Member, id=member_id)
        context = {
            "member": member,
            "dashboard": {
                "context": "shares",
                "title": "{} Shares".format(member.name),
                "buttons": [
                    {
                        "target": "#asm",
                        "title": "Add Share",
                        "class": "btn-primary",
                    },
                ],
            },
        }
        template = f"dashboard/records/index.html"
        return render(request, template, context)
