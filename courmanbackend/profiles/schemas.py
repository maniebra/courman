from typing import Optional

from ninja import ModelSchema, Schema

from profiles.models import Profile


class ProfileSchema(ModelSchema):
    username: str

    class Meta:
        model = Profile
        fields = ["id", "bio", "phone_number", "avatar", "created_at", "updated_at"]

    @staticmethod
    def resolve_username(obj: Profile) -> str:
        return obj.user.username


class ProfileUpdateSchema(Schema):
    bio: Optional[str] = None
    phone_number: Optional[str] = None
