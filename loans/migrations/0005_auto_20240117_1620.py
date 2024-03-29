# Generated by Django 3.2 on 2024-01-17 15:20

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('loans', '0004_loanrequest_guarantors'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='loanrepayment',
            options={'ordering': ['-created_at'], 'verbose_name_plural': 'Loan Repayments'},
        ),
        migrations.AlterModelOptions(
            name='loanrequest',
            options={'ordering': ['-created_at'], 'verbose_name_plural': 'Loan Requests'},
        ),
        migrations.RemoveField(
            model_name='loanrequest',
            name='guarantor_1',
        ),
        migrations.RemoveField(
            model_name='loanrequest',
            name='guarantor_2',
        ),
    ]
