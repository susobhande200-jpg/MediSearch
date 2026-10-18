from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
import os


class Command(BaseCommand):
    help = "Create or repair the configured Django superuser when explicitly enabled."

    def handle(self, *args, **options):
        if os.getenv("CREATE_ADMIN_ON_DEPLOY", "").strip() != "1":
            self.stdout.write("Admin bootstrap disabled; skipping.")
            return

        username = os.getenv("DJANGO_SUPERUSER_USERNAME", "").strip()
        email = os.getenv("DJANGO_SUPERUSER_EMAIL", "").strip()
        password = os.getenv("DJANGO_SUPERUSER_PASSWORD", "")

        if not username or not email or not password:
            raise CommandError(
                "Set DJANGO_SUPERUSER_USERNAME, DJANGO_SUPERUSER_EMAIL, "
                "and DJANGO_SUPERUSER_PASSWORD in the service environment."
            )
        if len(password) < 12:
            raise CommandError("DJANGO_SUPERUSER_PASSWORD must be at least 12 characters.")

        User = get_user_model()
        user, created = User.objects.get_or_create(
            username=username,
            defaults={"email": email, "is_staff": True, "is_superuser": True, "is_active": True},
        )

        # Repair permissions for an existing account. Password is only reset when
        # the explicit one-time RESET_ADMIN_PASSWORD=1 switch is enabled.
        changed = []
        if user.email != email:
            user.email = email
            changed.append("email")
        if not user.is_staff:
            user.is_staff = True
            changed.append("is_staff")
        if not user.is_superuser:
            user.is_superuser = True
            changed.append("is_superuser")
        if not user.is_active:
            user.is_active = True
            changed.append("is_active")

        if created or os.getenv("RESET_ADMIN_PASSWORD", "").strip() == "1":
            user.set_password(password)
            changed.append("password")

        if changed:
            user.save()

        if created:
            self.stdout.write(self.style.SUCCESS(f"Created superuser '{username}'."))
        else:
            self.stdout.write(self.style.SUCCESS(
                f"Superuser '{username}' is present; updated: {', '.join(changed) if changed else 'no changes'}."
            ))
