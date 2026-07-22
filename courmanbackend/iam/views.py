from django.contrib.auth import aauthenticate, alogin, alogout
from django.db import IntegrityError
from ninja import Router
from ninja.errors import HttpError
from ninja.pagination import paginate
from ninja.security import SessionAuth, SessionAuthIsStaff

from iam.models import Role, RoleAction, User
from iam.repository import RoleActionRepository, RoleRepository, UserRepository
from iam.schemas import (
    LoginSchema,
    MessageSchema,
    RoleActionCreateSchema,
    RoleActionSchema,
    RoleActionUpdateSchema,
    RoleCreateSchema,
    RoleSchema,
    RoleUpdateSchema,
    UserCreateSchema,
    UserSchema,
    UserUpdateSchema,
)

session_auth = SessionAuth()
staff_auth = SessionAuthIsStaff()


# --- auth -------------------------------------------------------------------

auth_router = Router(tags=["auth"])


@auth_router.post("/register", response={201: UserSchema})
async def register(request, payload: UserCreateSchema):
    try:
        user = await UserRepository.create_user(**payload.dict())
    except IntegrityError:
        raise HttpError(409, "A user with that username already exists")
    return 201, user


@auth_router.post("/login", response=UserSchema)
async def login(request, payload: LoginSchema):
    user = await aauthenticate(request, username=payload.username, password=payload.password)
    if user is None:
        raise HttpError(401, "Invalid credentials")
    await alogin(request, user)
    return await UserRepository.get_user(user.id)


@auth_router.post("/logout", response=MessageSchema, auth=session_auth)
async def logout(request):
    await alogout(request)
    return {"detail": "Logged out"}


@auth_router.get("/me", response=UserSchema, auth=session_auth)
async def me(request):
    return await UserRepository.get_user(request.auth.id)


# --- users --------------------------------------------------------------

users_router = Router(tags=["users"], auth=staff_auth)


@users_router.get("/", response=list[UserSchema])
@paginate
async def list_users(request):
    return UserRepository.list_users()


@users_router.get("/{user_id}", response=UserSchema)
async def get_user(request, user_id: int):
    try:
        return await UserRepository.get_user(user_id)
    except User.DoesNotExist:
        raise HttpError(404, "User not found")


@users_router.post("/", response={201: UserSchema})
async def create_user(request, payload: UserCreateSchema):
    try:
        user = await UserRepository.create_user(**payload.dict())
    except IntegrityError:
        raise HttpError(409, "A user with that username already exists")
    return 201, user


@users_router.patch("/{user_id}", response=UserSchema)
async def update_user(request, user_id: int, payload: UserUpdateSchema):
    try:
        user = await UserRepository.get_user(user_id)
    except User.DoesNotExist:
        raise HttpError(404, "User not found")
    return await UserRepository.update_user(user, **payload.dict(exclude_unset=True))


@users_router.delete("/{user_id}", response=MessageSchema)
async def delete_user(request, user_id: int):
    try:
        user = await UserRepository.get_user(user_id)
    except User.DoesNotExist:
        raise HttpError(404, "User not found")
    await UserRepository.delete_user(user)
    return {"detail": "User deleted"}


@users_router.post("/{user_id}/roles/{role_id}", response=UserSchema)
async def assign_role_to_user(request, user_id: int, role_id: int):
    try:
        user = await UserRepository.get_user(user_id)
    except User.DoesNotExist:
        raise HttpError(404, "User not found")
    try:
        role = await RoleRepository.get_role(role_id)
    except Role.DoesNotExist:
        raise HttpError(404, "Role not found")
    await UserRepository.add_role(user, role)
    return await UserRepository.get_user(user_id)


@users_router.delete("/{user_id}/roles/{role_id}", response=UserSchema)
async def remove_role_from_user(request, user_id: int, role_id: int):
    try:
        user = await UserRepository.get_user(user_id)
    except User.DoesNotExist:
        raise HttpError(404, "User not found")
    try:
        role = await RoleRepository.get_role(role_id)
    except Role.DoesNotExist:
        raise HttpError(404, "Role not found")
    await UserRepository.remove_role(user, role)
    return await UserRepository.get_user(user_id)


# --- roles --------------------------------------------------------------

roles_router = Router(tags=["roles"], auth=staff_auth)


@roles_router.get("/", response=list[RoleSchema])
@paginate
async def list_roles(request):
    return RoleRepository.list_roles()


@roles_router.get("/{role_id}", response=RoleSchema)
async def get_role(request, role_id: int):
    try:
        return await RoleRepository.get_role(role_id)
    except Role.DoesNotExist:
        raise HttpError(404, "Role not found")


@roles_router.post("/", response={201: RoleSchema})
async def create_role(request, payload: RoleCreateSchema):
    try:
        role = await RoleRepository.create_role(**payload.dict())
    except IntegrityError:
        raise HttpError(409, "A role with that name already exists")
    return 201, role


@roles_router.patch("/{role_id}", response=RoleSchema)
async def update_role(request, role_id: int, payload: RoleUpdateSchema):
    try:
        role = await RoleRepository.get_role(role_id)
    except Role.DoesNotExist:
        raise HttpError(404, "Role not found")
    try:
        return await RoleRepository.update_role(role, **payload.dict(exclude_unset=True))
    except IntegrityError:
        raise HttpError(409, "A role with that name already exists")


@roles_router.delete("/{role_id}", response=MessageSchema)
async def delete_role(request, role_id: int):
    try:
        role = await RoleRepository.get_role(role_id)
    except Role.DoesNotExist:
        raise HttpError(404, "Role not found")
    await RoleRepository.delete_role(role)
    return {"detail": "Role deleted"}


@roles_router.post("/{role_id}/actions/{action_id}", response=RoleSchema)
async def assign_action_to_role(request, role_id: int, action_id: int):
    try:
        role = await RoleRepository.get_role(role_id)
    except Role.DoesNotExist:
        raise HttpError(404, "Role not found")
    try:
        action = await RoleActionRepository.get_action(action_id)
    except RoleAction.DoesNotExist:
        raise HttpError(404, "Action not found")
    await RoleRepository.add_action(role, action)
    return await RoleRepository.get_role(role_id)


@roles_router.delete("/{role_id}/actions/{action_id}", response=RoleSchema)
async def remove_action_from_role(request, role_id: int, action_id: int):
    try:
        role = await RoleRepository.get_role(role_id)
    except Role.DoesNotExist:
        raise HttpError(404, "Role not found")
    try:
        action = await RoleActionRepository.get_action(action_id)
    except RoleAction.DoesNotExist:
        raise HttpError(404, "Action not found")
    await RoleRepository.remove_action(role, action)
    return await RoleRepository.get_role(role_id)


# --- role actions ---------------------------------------------------------

actions_router = Router(tags=["actions"], auth=staff_auth)


@actions_router.get("/", response=list[RoleActionSchema])
@paginate
async def list_actions(request):
    return RoleActionRepository.list_actions()


@actions_router.get("/{action_id}", response=RoleActionSchema)
async def get_action(request, action_id: int):
    try:
        return await RoleActionRepository.get_action(action_id)
    except RoleAction.DoesNotExist:
        raise HttpError(404, "Action not found")


@actions_router.post("/", response={201: RoleActionSchema})
async def create_action(request, payload: RoleActionCreateSchema):
    try:
        action = await RoleActionRepository.create_action(**payload.dict())
    except IntegrityError:
        raise HttpError(409, "An action with that name already exists")
    return 201, action


@actions_router.patch("/{action_id}", response=RoleActionSchema)
async def update_action(request, action_id: int, payload: RoleActionUpdateSchema):
    try:
        action = await RoleActionRepository.get_action(action_id)
    except RoleAction.DoesNotExist:
        raise HttpError(404, "Action not found")
    try:
        return await RoleActionRepository.update_action(action, **payload.dict(exclude_unset=True))
    except IntegrityError:
        raise HttpError(409, "An action with that name already exists")


@actions_router.delete("/{action_id}", response=MessageSchema)
async def delete_action(request, action_id: int):
    try:
        action = await RoleActionRepository.get_action(action_id)
    except RoleAction.DoesNotExist:
        raise HttpError(404, "Action not found")
    await RoleActionRepository.delete_action(action)
    return {"detail": "Action deleted"}


# --- combined router --------------------------------------------------------

api = Router()
api.add_router("/auth", auth_router)
api.add_router("/users", users_router)
api.add_router("/roles", roles_router)
api.add_router("/actions", actions_router)
