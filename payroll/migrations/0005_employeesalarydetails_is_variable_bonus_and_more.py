# Generated by Django 5.0.4 on 2025-07-11 06:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('payroll', '0004_payrollworkflow'),
    ]

    operations = [
        migrations.AddField(
            model_name='employeesalarydetails',
            name='is_variable_bonus',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='employeesalarydetails',
            name='variable_bonus',
            field=models.JSONField(blank=True, default=dict),
        ),
    ]
