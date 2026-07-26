import os

from django.core.management.base import BaseCommand

from iam.models import Role, User


class Command(BaseCommand):
    help = "Seed the Admin role and a superuser from ADMIN_USERNAME/ADMIN_PASSWORD."

    def handle(self, *args, **options):
        username = os.environ.get("ADMIN_USERNAME", "admin")
        password = os.environ.get("ADMIN_PASSWORD", "Admin@123")
        email = os.environ.get("ADMIN_EMAIL", "admin@example.com")

        role, _ = Role.objects.get_or_create(name="Admin")

        user, created = User.objects.get_or_create(
            username=username,
            defaults={"email": email, "is_staff": True, "is_superuser": True},
        )
        if created:
            user.set_password(password)
            user.save()
        user.roles.add(role)

        status = "created" if created else "already exists (password untouched)"
        self.stdout.write(f"Admin '{user.username}': {status}")
