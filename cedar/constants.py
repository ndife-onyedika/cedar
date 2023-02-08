import calendar


RELATIONSHIP_CHOICE = [
    ("parent", "Parent"),
    ("sibling", "Sibling"),
    ("caregiver", "Caregiver"),
    ("benefactor", "Benefactor"),
    ("other-relation", "Other Relation"),
]

LOAN_STATUS_CHOICES = [
    ("disbursed", "Disbursed"),
    ("terminated", "Terminated"),
]

CREDIT_REASON_CHOICES = [
    ("credit-deposit", "Deposit"),
    ("credit-eoy", "Year End Balance"),
]

DEBIT_REASON_CHOICES = [
    ("debit-withdrawal", "Withdrawal"),
]

MONTH_CHOICES = [(i, calendar.month_name[i]) for i in range(1, 13)]
