from ninja import File, Router
from ninja.files import UploadedFile
from ninja.pagination import paginate
from ninja.security import SessionAuth

from commons.crud import aget_or_404
from iam.actions import Actions
from iam.permissions import HasAction
from profiles.repository import ProfileRepository
from profiles.schemas import ProfileSchema, ProfileUpdateSchema

session_auth = SessionAuth()
view_users = HasAction(Actions.USERS_VIEW)

api = Router(tags=["profiles"])


@api.get("/me", response=ProfileSchema, auth=session_auth)
async def get_my_profile(request):
    return await ProfileRepository.get_or_create_profile(request.auth)


@api.patch("/me", response=ProfileSchema, auth=session_auth)
async def update_my_profile(request, payload: ProfileUpdateSchema):
    profile = await ProfileRepository.get_or_create_profile(request.auth)
    return await ProfileRepository.update_profile(profile, **payload.dict(exclude_unset=True))


@api.post("/me/avatar", response=ProfileSchema, auth=session_auth)
async def upload_my_avatar(request, avatar: UploadedFile = File(...)):
    profile = await ProfileRepository.get_or_create_profile(request.auth)
    return await ProfileRepository.update_profile(profile, avatar=avatar)


@api.get("/", response=list[ProfileSchema], auth=view_users)
@paginate
async def list_profiles(request):
    return ProfileRepository.list_profiles()


@api.get("/{user_id}", response=ProfileSchema, auth=view_users)
async def get_profile(request, user_id: int):
    return await aget_or_404(ProfileRepository.get_profile(user_id), "Profile not found")
