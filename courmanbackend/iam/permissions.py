from typing import Optional

from django.conf import settings
from django.http import HttpRequest
from ninja.security import APIKeyCookie

from iam.actions import ACTION_CATALOGUE
from iam.models import User


class HasAction(APIKeyCookie):
    """Session auth that additionally requires one of the given RoleActions.

    Superusers always pass. Usable as an `auth=` dependency on any router or
    operation, e.g. `auth=HasAction(Actions.COURSES_MANAGE)`. Passing several
    actions means "any of these", for endpoints that serve more than one role.
    """

    param_name: str = settings.SESSION_COOKIE_NAME

    def __init__(self, *action_names: str, csrf: bool = True) -> None:
        if not action_names:
            raise ValueError("HasAction needs at least one action name")
        self.action_names = action_names
        super().__init__(csrf=csrf)

    def authenticate(self, request: HttpRequest, key: Optional[str]) -> Optional[User]:
        user = request.user
        if not user.is_authenticated:
            return None
        if user.is_superuser:
            return user
        if user.roles.filter(actions__name__in=self.action_names).exists():
            return user
        return None


def actions_of(user: User) -> list[str]:
    """Every action a user holds, through any of their roles.

    Walks the `roles__actions` prefetch that `UserRepository` sets up rather than
    querying, so it is safe to call while serialising inside an async view.
    """
    if user.is_superuser:
        return sorted(ACTION_CATALOGUE)
    return sorted({action.name for role in user.roles.all() for action in role.actions.all()})
