# Generated by Django 2.1.2 on 2018-10-30 00:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('musicbot', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='message',
            name='payload',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name='conversation',
            name='state',
            field=models.CharField(choices=[('WELCOME', 0), ('MENU_OPTIONS', 1), ('MENU_FAV_LIST', 2), ('MENU_LYRICS', 3), ('FAV_SONGS', 4)], max_length=1),
        ),
    ]
