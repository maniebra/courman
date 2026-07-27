from typing import Literal, Optional

from ninja import ModelSchema, Schema

from iam.models import Role, RoleAction, User


class UserBriefSchema(ModelSchema):
    """Lightweight user representation for embedding in other apps' schemas.

    Unlike UserSchema, this excludes `roles` so callers don't need to
    prefetch_related("roles__actions") just to nest a user in a response.
    """

    class Meta:
        model = User
        fields = ["id", "username", "first_name", "last_name"]


class RoleActionSchema(ModelSchema):
    class Meta:
        model = RoleAction
        fields = ["id", "name", "created_at", "updated_at"]


class ActionCatalogueSchema(Schema):
    """An action the backend actually checks, and what holding it allows."""

    name: str
    description: str


class RoleActionCreateSchema(Schema):
    name: str


class RoleActionUpdateSchema(Schema):
    name: Optional[str] = None


class RoleSchema(ModelSchema):
    actions: list[RoleActionSchema] = []

    class Meta:
        model = Role
        fields = ["id", "name", "created_at", "updated_at"]


class RoleCreateSchema(Schema):
    name: str


class RoleUpdateSchema(Schema):
    name: Optional[str] = None


class UserSchema(ModelSchema):
    roles: list[RoleSchema] = []
    #: flattened from the user's roles so callers never have to walk them
    actions: list[str] = []

    @staticmethod
    def resolve_actions(obj: User) -> list[str]:
        from iam.permissions import actions_of

        return actions_of(obj)

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "first_name",
            "last_name",
            "email",
            "is_active",
            "is_staff",
            "is_superuser",
            "date_joined",
        ]


class UserCreateSchema(Schema):
    username: str
    password: str
    email: str = ""
    first_name: str = ""
    last_name: str = ""


class UserUpdateSchema(Schema):
    email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    is_active: Optional[bool] = None


class LoginSchema(Schema):
    username: str
    password: str


class MessageSchema(Schema):
    detail: str


class AppSettingsSchema(Schema):
    """The settings that apply to every user, not just the caller."""

    language: str


class AppSettingsUpdateSchema(Schema):
    language: Literal["en", "fa"]
