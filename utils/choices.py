import calendar

from django.db import models
from django.utils.translation import gettext_lazy as _

MONTH_CHOICES = [(i, calendar.month_name[i]) for i in range(1, 13)]


class RelationshipChoice(models.TextChoices):
    PARENT = "parent", _("Parent")
    SIBLING = "sibling", _("Sibling")
    CAREGIVER = "caregiver", _("Caregiver")
    BENEFACTOR = "benefactor", _("Benefactor")
    OTHER_RELATION = "other-relation", _("Other Relation")


class LoanStatusChoice(models.TextChoices):
    DISBURSED = "disbursed", _("Disbursed")
    TERMINATED = "terminated", _("Terminated")


class CreditReasonChoice(models.TextChoices):
    DEPOSIT = "credit-deposit", _("Deposit")
    END_OF_YEAR = "credit-eoy", _("Year End Balance")


class DebitReasonChoice(models.TextChoices):
    WITHDRAWAL = "debit-withdrawal", _("Withdrawal")
