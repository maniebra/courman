from iam.models import Role, RoleAction, User


class UserRepository:
    @staticmethod
    def list_users():
        return User.objects.prefetch_related("roles__actions").all()

    @staticmethod
    async def get_user(user_id: int) -> User:
        return await User.objects.prefetch_related("roles__actions").aget(pk=user_id)

    @staticmethod
    async def create_user(*, username: str, password: str, email: str = "", first_name: str = "", last_name: str = "") -> User:
        user = await User.objects.acreate_user(
            username=username,
            password=password,
            email=email,
            first_name=first_name,
            last_name=last_name,
        )
        return await UserRepository.get_user(user.id)

    @staticmethod
    async def update_user(user: User, **fields) -> User:
        for field, value in fields.items():
            if value is not None:
                setattr(user, field, value)
        await user.asave()
        return user

    @staticmethod
    async def delete_user(user: User) -> None:
        await user.adelete()

    @staticmethod
    async def add_role(user: User, role: Role) -> None:
        await user.roles.aadd(role)

    @staticmethod
    async def remove_role(user: User, role: Role) -> None:
        await user.roles.aremove(role)

    @staticmethod
    async def has_action(user: User, action_name: str) -> bool:
        if user.is_superuser:
            return True
        return await RoleAction.objects.filter(
            name=action_name, roles__users=user
        ).aexists()


class RoleRepository:
    @staticmethod
    def list_roles():
        return Role.objects.prefetch_related("actions").all()

    @staticmethod
    async def get_role(role_id: int) -> Role:
        return await Role.objects.prefetch_related("actions").aget(pk=role_id)

    @staticmethod
    async def create_role(*, name: str) -> Role:
        role = await Role.objects.acreate(name=name)
        return await RoleRepository.get_role(role.id)

    @staticmethod
    async def update_role(role: Role, **fields) -> Role:
        for field, value in fields.items():
            if value is not None:
                setattr(role, field, value)
        await role.asave()
        return role

    @staticmethod
    async def delete_role(role: Role) -> None:
        await role.adelete()

    @staticmethod
    async def add_action(role: Role, action: RoleAction) -> None:
        await role.actions.aadd(action)

    @staticmethod
    async def remove_action(role: Role, action: RoleAction) -> None:
        await role.actions.aremove(action)


class RoleActionRepository:
    @staticmethod
    def list_actions():
        return RoleAction.objects.all()

    @staticmethod
    async def get_action(action_id: int) -> RoleAction:
        return await RoleAction.objects.aget(pk=action_id)

    @staticmethod
    async def create_action(*, name: str) -> RoleAction:
        return await RoleAction.objects.acreate(name=name)

    @staticmethod
    async def update_action(action: RoleAction, **fields) -> RoleAction:
        for field, value in fields.items():
            if value is not None:
                setattr(action, field, value)
        await action.asave()
        return action

    @staticmethod
    async def delete_action(action: RoleAction) -> None:
        await action.adelete()
