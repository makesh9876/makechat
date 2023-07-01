# Generated by Django 4.2.2 on 2023-06-24 15:26

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("chatgpt", "0003_alter_usermessage_role"),
    ]

    operations = [
        migrations.CreateModel(
            name="InvitedUsers",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("invite_to", models.CharField(max_length=20)),
                ("onboarded", models.BooleanField(default=False)),
                ("invited_at", models.DateTimeField(default=django.utils.timezone.now)),
                (
                    "onboarded_at",
                    models.DateTimeField(default=django.utils.timezone.now),
                ),
                (
                    "invite_from",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
    ]
