# Generated by Django 3.2 on 2024-01-17 15:20

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('savings', '0003_auto_20230319_1933'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='savingscredit',
            options={'ordering': ['-created_at'], 'verbose_name_plural': 'Savings Credit'},
        ),
        migrations.AlterModelOptions(
            name='savingsdebit',
            options={'ordering': ['-created_at'], 'verbose_name_plural': 'Savings Debit'},
        ),
        migrations.AlterModelOptions(
            name='savingsinterest',
            options={'ordering': ['-created_at', 'member__name', '-total_interest'], 'verbose_name_plural': 'Savings Interests'},
        ),
        migrations.AlterModelOptions(
            name='savingsinteresttotal',
            options={'ordering': ['member__name', '-created_at'], 'verbose_name_plural': 'Savings Interests Total'},
        ),
        migrations.AlterModelOptions(
            name='yearendbalance',
            options={'ordering': ['-created_at', 'member__name'], 'verbose_name': 'Year End Balance', 'verbose_name_plural': 'Year End Balances'},
        ),
    ]
