from typing import Optional

from django.conf import settings
from django.http import HttpRequest
from ninja.security import APIKeyCookie

from iam.models import User


class HasAction(APIKeyCookie):
    """Session auth that additionally requires the user to hold a given RoleAction.

    Superusers always pass. Usable as an `auth=` dependency on any router/operation,
    e.g. `auth=HasAction("courses.publish")`.
    """

    param_name: str = settings.SESSION_COOKIE_NAME

    def __init__(self, action_name: str, csrf: bool = True) -> None:
        self.action_name = action_name
        super().__init__(csrf=csrf)

    def authenticate(self, request: HttpRequest, key: Optional[str]) -> Optional[User]:
        user = request.user
        if not user.is_authenticated:
            return None
        if user.is_superuser:
            return user
        if user.roles.filter(actions__name=self.action_name).exists():
            return user
        return None
