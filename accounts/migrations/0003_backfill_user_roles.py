from django.db import migrations


def backfill_roles(apps, schema_editor):
    User = apps.get_model("accounts", "User")

    for user in User.objects.all():
        role = "staff"
        email = (user.email or "").lower()
        name = (user.name or "").lower()

        if user.is_superuser or user.is_staff:
            role = "admin"
        elif "doctor" in email or name.startswith("dr"):
            role = "doctor"
        elif "ops" in email or "operations" in name:
            role = "ops"

        user.role = role
        user.save(update_fields=["role"])


def noop_reverse(apps, schema_editor):
    return


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0002_user_role"),
    ]

    operations = [
        migrations.RunPython(backfill_roles, noop_reverse),
    ]
