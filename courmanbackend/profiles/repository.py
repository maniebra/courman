from iam.models import User
from profiles.models import Profile


class ProfileRepository:
    @staticmethod
    def list_profiles():
        return Profile.objects.select_related("user").all()

    @staticmethod
    async def get_profile(user_id: int) -> Profile:
        return await Profile.objects.select_related("user").aget(user_id=user_id)

    @staticmethod
    async def get_or_create_profile(user: User) -> Profile:
        profile, _ = await Profile.objects.select_related("user").aget_or_create(user=user)
        return profile

    @staticmethod
    async def update_profile(profile: Profile, **fields) -> Profile:
        for field, value in fields.items():
            if value is not None:
                setattr(profile, field, value)
        await profile.asave()
        return profile
