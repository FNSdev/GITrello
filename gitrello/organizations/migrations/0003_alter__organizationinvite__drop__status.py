# Generated by Django 3.1.1 on 2020-09-26 10:58

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('organizations', '0002_auto_20200524_1339'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='organizationinvite',
            name='status',
        ),
    ]
