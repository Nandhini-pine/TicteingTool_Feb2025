# Generated by Django 4.2.4 on 2024-12-13 10:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tickets', '0052_alter_seekclarificationhistory_seek_comment'),
    ]

    operations = [
        migrations.AddField(
            model_name='approvalmatrix',
            name='is_active',
            field=models.BooleanField(default=True, help_text='Indicates if the approval matrix is active'),
        ),
    ]
