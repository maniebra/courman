from typing import Optional

from ninja import ModelSchema, Schema

from iam.models import Role, RoleAction, User


class RoleActionSchema(ModelSchema):
    class Meta:
        model = RoleAction
        fields = ["id", "name", "created_at", "updated_at"]


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
