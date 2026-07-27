from django.contrib.auth import aauthenticate, alogin, alogout
from django.db import IntegrityError
from django.middleware.csrf import get_token
from ninja import Router
from ninja.errors import HttpError
from ninja.pagination import paginate
from ninja.security import SessionAuth

from commons.crud import ModelCrudView, aget_or_404
from iam.models import AppSettings, Role, RoleAction, User
from iam.actions import ACTION_CATALOGUE, Actions
from iam.permissions import HasAction
from iam.repository import RoleActionRepository, RoleRepository, UserRepository
from iam.schemas import (
    AppSettingsSchema,
    AppSettingsUpdateSchema,
    ActionCatalogueSchema,
    UserBriefSchema,
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
view_users = HasAction(Actions.USERS_VIEW)
manage_users = HasAction(Actions.USERS_MANAGE)
view_roles = HasAction(Actions.ROLES_VIEW)
manage_roles = HasAction(Actions.ROLES_MANAGE)


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
    # Session-authed endpoints check CSRF, but the cookie is only ever sent to
    # the browser once something calls get_token() - do it here so the SPA
    # has a token for the mutating requests it makes right after login.
    get_token(request)
    return await UserRepository.get_user(user.id)


@auth_router.post("/logout", response=MessageSchema, auth=session_auth)
async def logout(request):
    await alogout(request)
    return {"detail": "Logged out"}


@auth_router.get("/me", response=UserSchema, auth=session_auth)
async def me(request):
    get_token(request)
    return await UserRepository.get_user(request.auth.id)


# --- users --------------------------------------------------------------

users_router = Router(tags=["users"], auth=view_users)


class UserCrud(ModelCrudView[User]):
    schema = UserSchema
    create_schema = UserCreateSchema
    update_schema = UserUpdateSchema
    list_fn = staticmethod(UserRepository.list_users)
    get_fn = staticmethod(UserRepository.get_user)
    create_fn = staticmethod(UserRepository.create_user)
    update_fn = staticmethod(UserRepository.update_user)
    delete_fn = staticmethod(UserRepository.delete_user)
    not_found_message = "User not found"
    conflict_message = "A user with that username already exists"
    deleted_message = "User deleted"


user_crud = UserCrud()


@users_router.get("/", response=list[UserCrud.schema])
@paginate
async def list_users(request):
    return user_crud.list()


@users_router.get("/lookup", response=list[UserBriefSchema], auth=view_users)
async def lookup_users(request, q: str = "", limit: int = 20):
    """Username search for anyone holding `users.view`.

    Course managers need to pick people (staff, graders) without being able to
    edit accounts, so this returns the brief representation only - no roles, no
    email - and the Professor and Head TA roles are seeded with `users.view`.
    """
    users = UserRepository.list_users()
    if q:
        users = users.filter(username__icontains=q)
    return [user async for user in users[: min(limit, 50)]]


@users_router.get("/{user_id}", response=UserCrud.schema)
async def get_user(request, user_id: int):
    return await user_crud.retrieve(user_id)


@users_router.post("/", response={201: UserCrud.schema}, auth=manage_users)
async def create_user(request, payload: UserCrud.create_schema):
    return 201, await user_crud.create(payload)


@users_router.patch("/{user_id}", response=UserCrud.schema, auth=manage_users)
async def update_user(request, user_id: int, payload: UserCrud.update_schema):
    return await user_crud.update(user_id, payload)


@users_router.delete("/{user_id}", response=MessageSchema, auth=manage_users)
async def delete_user(request, user_id: int):
    return await user_crud.destroy(user_id)


@users_router.post("/{user_id}/roles/{role_id}", response=UserSchema, auth=manage_users)
async def assign_role_to_user(request, user_id: int, role_id: int):
    user = await aget_or_404(UserRepository.get_user(user_id), "User not found")
    role = await aget_or_404(RoleRepository.get_role(role_id), "Role not found")
    await UserRepository.add_role(user, role)
    return await UserRepository.get_user(user_id)


@users_router.delete("/{user_id}/roles/{role_id}", response=UserSchema, auth=manage_users)
async def remove_role_from_user(request, user_id: int, role_id: int):
    user = await aget_or_404(UserRepository.get_user(user_id), "User not found")
    role = await aget_or_404(RoleRepository.get_role(role_id), "Role not found")
    await UserRepository.remove_role(user, role)
    return await UserRepository.get_user(user_id)


# --- roles --------------------------------------------------------------

roles_router = Router(tags=["roles"], auth=view_roles)


class RoleCrud(ModelCrudView[Role]):
    schema = RoleSchema
    create_schema = RoleCreateSchema
    update_schema = RoleUpdateSchema
    list_fn = staticmethod(RoleRepository.list_roles)
    get_fn = staticmethod(RoleRepository.get_role)
    create_fn = staticmethod(RoleRepository.create_role)
    update_fn = staticmethod(RoleRepository.update_role)
    delete_fn = staticmethod(RoleRepository.delete_role)
    not_found_message = "Role not found"
    conflict_message = "A role with that name already exists"
    deleted_message = "Role deleted"


role_crud = RoleCrud()


@roles_router.get("/", response=list[RoleCrud.schema])
@paginate
async def list_roles(request):
    return role_crud.list()


@roles_router.get("/{role_id}", response=RoleCrud.schema)
async def get_role(request, role_id: int):
    return await role_crud.retrieve(role_id)


@roles_router.post("/", response={201: RoleCrud.schema}, auth=manage_roles)
async def create_role(request, payload: RoleCrud.create_schema):
    return 201, await role_crud.create(payload)


@roles_router.patch("/{role_id}", response=RoleCrud.schema, auth=manage_roles)
async def update_role(request, role_id: int, payload: RoleCrud.update_schema):
    return await role_crud.update(role_id, payload)


@roles_router.delete("/{role_id}", response=MessageSchema, auth=manage_roles)
async def delete_role(request, role_id: int):
    return await role_crud.destroy(role_id)


@roles_router.post("/{role_id}/actions/{action_id}", response=RoleSchema, auth=manage_roles)
async def assign_action_to_role(request, role_id: int, action_id: int):
    role = await aget_or_404(RoleRepository.get_role(role_id), "Role not found")
    action = await aget_or_404(RoleActionRepository.get_action(action_id), "Action not found")
    await RoleRepository.add_action(role, action)
    return await RoleRepository.get_role(role_id)


@roles_router.delete("/{role_id}/actions/{action_id}", response=RoleSchema, auth=manage_roles)
async def remove_action_from_role(request, role_id: int, action_id: int):
    role = await aget_or_404(RoleRepository.get_role(role_id), "Role not found")
    action = await aget_or_404(RoleActionRepository.get_action(action_id), "Action not found")
    await RoleRepository.remove_action(role, action)
    return await RoleRepository.get_role(role_id)


# --- role actions ---------------------------------------------------------

actions_router = Router(tags=["actions"], auth=view_roles)


class ActionCrud(ModelCrudView[RoleAction]):
    schema = RoleActionSchema
    create_schema = RoleActionCreateSchema
    update_schema = RoleActionUpdateSchema
    list_fn = staticmethod(RoleActionRepository.list_actions)
    get_fn = staticmethod(RoleActionRepository.get_action)
    create_fn = staticmethod(RoleActionRepository.create_action)
    update_fn = staticmethod(RoleActionRepository.update_action)
    delete_fn = staticmethod(RoleActionRepository.delete_action)
    not_found_message = "Action not found"
    conflict_message = "An action with that name already exists"
    deleted_message = "Action deleted"


action_crud = ActionCrud()


@actions_router.get("/", response=list[ActionCrud.schema])
@paginate
async def list_actions(request):
    return action_crud.list()


@actions_router.get("/catalogue", response=list[ActionCatalogueSchema])
async def action_catalogue(request):
    """The action names the API enforces.

    Rows in the actions table are free text, so anything outside this list is
    stored but never checked - the UI uses this to tell the two apart.
    """
    return [{"name": name, "description": description} for name, description in ACTION_CATALOGUE.items()]


@actions_router.get("/{action_id}", response=ActionCrud.schema)
async def get_action(request, action_id: int):
    return await action_crud.retrieve(action_id)


@actions_router.post("/", response={201: ActionCrud.schema}, auth=manage_roles)
async def create_action(request, payload: ActionCrud.create_schema):
    return 201, await action_crud.create(payload)


@actions_router.patch("/{action_id}", response=ActionCrud.schema, auth=manage_roles)
async def update_action(request, action_id: int, payload: ActionCrud.update_schema):
    return await action_crud.update(action_id, payload)


@actions_router.delete("/{action_id}", response=MessageSchema, auth=manage_roles)
async def delete_action(request, action_id: int):
    return await action_crud.destroy(action_id)


# --- app settings -----------------------------------------------------------

settings_router = Router(tags=["settings"])


async def _app_settings() -> AppSettings:
    """The single settings row, seeded from APP_DEFAULT_LANGUAGE on first read."""
    row, _ = await AppSettings.objects.aget_or_create(pk=1)
    return row


@settings_router.get("/", response=AppSettingsSchema)
async def get_app_settings(request):
    # Unauthenticated: the sign-in page needs the language before anyone logs in.
    return await _app_settings()


@settings_router.put("/", response=AppSettingsSchema, auth=HasAction(Actions.SETTINGS_MANAGE))
async def update_app_settings(request, payload: AppSettingsUpdateSchema):
    row = await _app_settings()
    row.language = payload.language
    await row.asave()
    return row


# --- combined router --------------------------------------------------------

api = Router()
api.add_router("/auth", auth_router)
api.add_router("/users", users_router)
api.add_router("/roles", roles_router)
api.add_router("/actions", actions_router)
api.add_router("/settings", settings_router)
