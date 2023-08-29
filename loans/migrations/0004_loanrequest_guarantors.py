# Generated by Django 3.2 on 2023-08-26 06:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
        ('loans', '0003_auto_20230311_1444'),
    ]

    operations = [
        migrations.AddField(
            model_name='loanrequest',
            name='guarantors',
            field=models.ManyToManyField(blank=True, related_name='loan_guarantors', to='accounts.Member'),
        ),
    ]
