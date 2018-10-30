# Generated by Django 2.1.2 on 2018-10-29 20:19

from django.db import migrations, models
import django.db.models.deletion
import django_extensions.db.fields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Conversation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name='created')),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name='modified')),
                ('fb_user_id', models.CharField(max_length=100)),
                ('state', models.CharField(choices=[('WELCOME', 0), ('MENU_OPTIONS', 1)], max_length=1)),
            ],
            options={
                'ordering': ['-created'],
            },
        ),
        migrations.CreateModel(
            name='Message',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name='created')),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name='modified')),
                ('text', models.CharField(blank=True, max_length=500, null=True)),
                ('conversation', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='musicbot.Conversation')),
            ],
            options={
                'ordering': ['-created'],
            },
        ),
        migrations.CreateModel(
            name='Track',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('track_id', models.CharField(max_length=100)),
                ('conversation', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='musicbot.Conversation')),
            ],
        ),
    ]
