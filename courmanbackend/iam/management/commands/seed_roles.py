from django.core.management.base import BaseCommand

from iam.models import Role

COURSE_ROLES = ["Professor", "Head TA", "TA"]


class Command(BaseCommand):
    help = "Seed the default course roles (Professor, Head TA, TA)."

    def handle(self, *args, **options):
        for name in COURSE_ROLES:
            role, created = Role.objects.get_or_create(name=name)
            status = "created" if created else "already exists"
            self.stdout.write(f"Role '{role.name}': {status}")
