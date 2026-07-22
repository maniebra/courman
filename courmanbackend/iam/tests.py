import json

from django.test import TestCase

from iam.models import Role, RoleAction, User


def _json(response):
    return json.loads(response.content)


class AuthFlowTests(TestCase):
    async def test_register_creates_user(self):
        response = await self.async_client.post(
            "/api/iam/auth/register",
            data={"username": "alice", "password": "s3cret-pass"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(_json(response)["username"], "alice")
        self.assertTrue(await User.objects.filter(username="alice").aexists())

    async def test_register_duplicate_username_conflicts(self):
        await User.objects.acreate_user(username="alice", password="s3cret-pass")
        response = await self.async_client.post(
            "/api/iam/auth/register",
            data={"username": "alice", "password": "other-pass"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 409)

    async def test_login_logout_and_me(self):
        await User.objects.acreate_user(username="alice", password="s3cret-pass")

        me_response = await self.async_client.get("/api/iam/auth/me")
        self.assertEqual(me_response.status_code, 401)

        login_response = await self.async_client.post(
            "/api/iam/auth/login",
            data={"username": "alice", "password": "s3cret-pass"},
            content_type="application/json",
        )
        self.assertEqual(login_response.status_code, 200)
        self.assertEqual(_json(login_response)["username"], "alice")

        me_response = await self.async_client.get("/api/iam/auth/me")
        self.assertEqual(me_response.status_code, 200)
        self.assertEqual(_json(me_response)["username"], "alice")

        logout_response = await self.async_client.post("/api/iam/auth/logout")
        self.assertEqual(logout_response.status_code, 200)

        me_response = await self.async_client.get("/api/iam/auth/me")
        self.assertEqual(me_response.status_code, 401)

    async def test_login_invalid_credentials(self):
        await User.objects.acreate_user(username="alice", password="s3cret-pass")
        response = await self.async_client.post(
            "/api/iam/auth/login",
            data={"username": "alice", "password": "wrong-pass"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 401)


class UserManagementTests(TestCase):
    async def _login_staff(self):
        staff = await User.objects.acreate_user(username="admin", password="s3cret-pass", is_staff=True)
        await self.async_client.post(
            "/api/iam/auth/login",
            data={"username": "admin", "password": "s3cret-pass"},
            content_type="application/json",
        )
        return staff

    async def test_list_users_requires_staff(self):
        await User.objects.acreate_user(username="bob", password="s3cret-pass")
        response = await self.async_client.get("/api/iam/users/")
        self.assertEqual(response.status_code, 401)

        await self.async_client.post(
            "/api/iam/auth/login",
            data={"username": "bob", "password": "s3cret-pass"},
            content_type="application/json",
        )
        response = await self.async_client.get("/api/iam/users/")
        self.assertEqual(response.status_code, 401)

    async def test_staff_can_crud_users(self):
        await self._login_staff()

        create_response = await self.async_client.post(
            "/api/iam/users/",
            data={"username": "carol", "password": "s3cret-pass", "first_name": "Carol"},
            content_type="application/json",
        )
        self.assertEqual(create_response.status_code, 201)
        user_id = _json(create_response)["id"]

        get_response = await self.async_client.get(f"/api/iam/users/{user_id}")
        self.assertEqual(get_response.status_code, 200)
        self.assertEqual(_json(get_response)["first_name"], "Carol")

        update_response = await self.async_client.patch(
            f"/api/iam/users/{user_id}",
            data={"first_name": "Caroline"},
            content_type="application/json",
        )
        self.assertEqual(update_response.status_code, 200)
        self.assertEqual(_json(update_response)["first_name"], "Caroline")

        delete_response = await self.async_client.delete(f"/api/iam/users/{user_id}")
        self.assertEqual(delete_response.status_code, 200)
        self.assertFalse(await User.objects.filter(id=user_id).aexists())

    async def test_assign_and_remove_role(self):
        await self._login_staff()
        user = await User.objects.acreate_user(username="dave", password="s3cret-pass")
        role = await Role.objects.acreate(name="editor")

        assign_response = await self.async_client.post(f"/api/iam/users/{user.id}/roles/{role.id}")
        self.assertEqual(assign_response.status_code, 200)
        self.assertEqual([r["name"] for r in _json(assign_response)["roles"]], ["editor"])

        remove_response = await self.async_client.delete(f"/api/iam/users/{user.id}/roles/{role.id}")
        self.assertEqual(remove_response.status_code, 200)
        self.assertEqual(_json(remove_response)["roles"], [])


class RoleAndActionTests(TestCase):
    async def _login_staff(self):
        await User.objects.acreate_user(username="admin", password="s3cret-pass", is_staff=True)
        await self.async_client.post(
            "/api/iam/auth/login",
            data={"username": "admin", "password": "s3cret-pass"},
            content_type="application/json",
        )

    async def test_role_and_action_crud(self):
        await self._login_staff()

        action_response = await self.async_client.post(
            "/api/iam/actions/", data={"name": "courses.publish"}, content_type="application/json"
        )
        self.assertEqual(action_response.status_code, 201)
        action_id = _json(action_response)["id"]

        role_response = await self.async_client.post(
            "/api/iam/roles/", data={"name": "publisher"}, content_type="application/json"
        )
        self.assertEqual(role_response.status_code, 201)
        role_id = _json(role_response)["id"]

        attach_response = await self.async_client.post(f"/api/iam/roles/{role_id}/actions/{action_id}")
        self.assertEqual(attach_response.status_code, 200)
        self.assertEqual([a["name"] for a in _json(attach_response)["actions"]], ["courses.publish"])

        detach_response = await self.async_client.delete(f"/api/iam/roles/{role_id}/actions/{action_id}")
        self.assertEqual(detach_response.status_code, 200)
        self.assertEqual(_json(detach_response)["actions"], [])

        delete_role_response = await self.async_client.delete(f"/api/iam/roles/{role_id}")
        self.assertEqual(delete_role_response.status_code, 200)
        self.assertFalse(await Role.objects.filter(id=role_id).aexists())

    async def test_duplicate_role_name_conflicts(self):
        await self._login_staff()
        await Role.objects.acreate(name="publisher")
        response = await self.async_client.post(
            "/api/iam/roles/", data={"name": "publisher"}, content_type="application/json"
        )
        self.assertEqual(response.status_code, 409)


class HasActionPermissionTests(TestCase):
    async def test_user_has_action_via_role(self):
        user = await User.objects.acreate_user(username="erin", password="s3cret-pass")
        role = await Role.objects.acreate(name="publisher")
        action = await RoleAction.objects.acreate(name="courses.publish")
        await role.actions.aadd(action)
        await user.roles.aadd(role)

        from iam.repository import UserRepository

        self.assertTrue(await UserRepository.has_action(user, "courses.publish"))
        self.assertFalse(await UserRepository.has_action(user, "courses.delete"))

    async def test_superuser_has_every_action(self):
        user = await User.objects.acreate_superuser(username="root", password="s3cret-pass")

        from iam.repository import UserRepository

        self.assertTrue(await UserRepository.has_action(user, "anything.at.all"))
