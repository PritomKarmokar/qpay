from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

User = get_user_model()

DEFAULT_ADMINS = [
    {"username": "admin", "email": "admin@example.com", "password": "admin"},
    {"username": "testadmin", "email": "testadmin@example.com", "password": "test12345"},
    {"username": "staffuser", "email": "staff@example.com", "password": "staff12345", "is_superuser": False},
]


class Command(BaseCommand):
    """
    Create default admin/staff users for development and testing.
        NOTES
        - Safe to run multiple times; existing users are skipped, not modified.
        - Passwords are hashed with set_password().
        - Never enable DEV_MODE in production.
    """
    help = "Create default admin/staff users for development and testing (requires DEV_MODE=True)"

    def handle(self, *args, **options):
        if getattr(settings, "DEV_MODE", False) is not True:
            raise CommandError(
                "This command can only be run when DEV_MODE=True. "
                "Refusing to create default users with known passwords."
            )

        for data in DEFAULT_ADMINS:
            data = data.copy()
            username = data.pop("username")
            password = data.pop("password")
            is_superuser = data.pop("is_superuser", True)

            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    **data,
                    "is_staff": True,
                    "is_superuser": is_superuser,
                },
            )

            if created:
                user.set_password(password)
                user.save()
                self.stdout.write(self.style.SUCCESS(f"Created: {username}"))
            else:
                self.stdout.write(self.style.WARNING(f"Already exists: {username}"))

    """
    USAGE
        python manage.py seed_admin
    """