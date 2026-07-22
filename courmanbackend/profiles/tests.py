import json

from django.test import TestCase

from iam.models import User
from profiles.models import Profile


def _json(response):
    return json.loads(response.content)


class ProfileSelfServiceTests(TestCase):
    async def _login(self, username="alice"):
        await User.objects.acreate_user(username=username, password="s3cret-pass")
        await self.async_client.post(
            "/api/iam/auth/login",
            data={"username": username, "password": "s3cret-pass"},
            content_type="application/json",
        )

    async def test_get_my_profile_requires_auth(self):
        response = await self.async_client.get("/api/profiles/me")
        self.assertEqual(response.status_code, 401)

    async def test_get_my_profile_creates_on_first_access(self):
        await self._login()
        response = await self.async_client.get("/api/profiles/me")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(_json(response)["username"], "alice")
        self.assertTrue(await Profile.objects.filter(user__username="alice").aexists())

    async def test_update_my_profile(self):
        await self._login()
        response = await self.async_client.patch(
            "/api/profiles/me",
            data={"bio": "Hello there", "phone_number": "123456"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        body = _json(response)
        self.assertEqual(body["bio"], "Hello there")
        self.assertEqual(body["phone_number"], "123456")


class ProfileAdminTests(TestCase):
    async def _login_staff(self):
        await User.objects.acreate_user(username="admin", password="s3cret-pass", is_staff=True)
        await self.async_client.post(
            "/api/iam/auth/login",
            data={"username": "admin", "password": "s3cret-pass"},
            content_type="application/json",
        )

    async def test_list_profiles_requires_staff(self):
        response = await self.async_client.get("/api/profiles/")
        self.assertEqual(response.status_code, 401)

    async def test_staff_can_get_any_profile(self):
        user = await User.objects.acreate_user(username="bob", password="s3cret-pass")
        await Profile.objects.acreate(user=user, bio="Bob's bio")

        await self._login_staff()
        response = await self.async_client.get(f"/api/profiles/{user.id}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(_json(response)["bio"], "Bob's bio")

    async def test_get_missing_profile_404s(self):
        await self._login_staff()
        response = await self.async_client.get("/api/profiles/999999")
        self.assertEqual(response.status_code, 404)
