# Generated by Django 3.2 on 2023-02-21 11:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('loans', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='loanrequest',
            name='terminated_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
