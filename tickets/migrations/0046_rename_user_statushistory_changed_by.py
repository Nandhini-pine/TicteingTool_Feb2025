# Generated by Django 5.0.6 on 2024-10-05 04:16

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tickets', '0045_rename_changed_by_statushistory_user'),
    ]

    operations = [
        migrations.RenameField(
            model_name='statushistory',
            old_name='user',
            new_name='changed_by',
        ),
    ]
