# Generated by Django 3.2 on 2023-03-11 13:44

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
        ('loans', '0002_auto_20230311_1355'),
    ]

    operations = [
        migrations.AlterField(
            model_name='loanrequest',
            name='guarantor_1',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='guarantor_1', to='accounts.member'),
        ),
        migrations.AlterField(
            model_name='loanrequest',
            name='guarantor_2',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='guarantor_2', to='accounts.member'),
        ),
    ]
