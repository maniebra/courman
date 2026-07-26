from django.core.management.base import BaseCommand

from iam.actions import ACTION_CATALOGUE, ROLE_ACTIONS
from iam.models import Role, RoleAction


class Command(BaseCommand):
    help = "Seed the action catalogue and the default roles that hold them."

    def handle(self, *args, **options):
        actions = {}
        for name in ACTION_CATALOGUE:
            action, created = RoleAction.objects.get_or_create(name=name)
            actions[name] = action
            self.stdout.write(f"Action '{name}': {'created' if created else 'already exists'}")

        for role_name, action_names in ROLE_ACTIONS.items():
            role, created = Role.objects.get_or_create(name=role_name)
            # add, never remove: an operator may have granted extra actions on purpose
            role.actions.add(*[actions[name] for name in action_names])
            self.stdout.write(
                f"Role '{role.name}': {'created' if created else 'already exists'}"
                f" ({len(action_names)} actions ensured)"
            )
