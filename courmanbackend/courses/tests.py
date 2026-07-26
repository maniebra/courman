import json

from django.test import TestCase

from courses.models import Course, Student
from iam.models import User


def _json(response):
    return json.loads(response.content)


class CourseCrudTests(TestCase):
    async def _login_admin(self, *actions):
        """Sign in as someone whose role holds `actions` (all of them by default)."""
        from iam.actions import ACTION_CATALOGUE
        from iam.models import Role, RoleAction

        user = await User.objects.acreate_user(username="admin", password="s3cret-pass")
        role = await Role.objects.acreate(name="Test role")
        for name in actions or ACTION_CATALOGUE:
            action, _ = await RoleAction.objects.aget_or_create(name=name)
            await role.actions.aadd(action)
        await user.roles.aadd(role)
        await self.async_client.post(
            "/api/iam/auth/login",
            data={"username": "admin", "password": "s3cret-pass"},
            content_type="application/json",
        )
        return user

    async def _login(self, username="alice"):
        await User.objects.acreate_user(username=username, password="s3cret-pass")
        await self.async_client.post(
            "/api/iam/auth/login",
            data={"username": username, "password": "s3cret-pass"},
            content_type="application/json",
        )

    async def test_list_courses_requires_auth(self):
        response = await self.async_client.get("/api/courses/")
        self.assertEqual(response.status_code, 401)

    async def test_create_course_requires_staff(self):
        await self._login()
        response = await self.async_client.post(
            "/api/courses/",
            data={"code": "CS101", "name": "Intro to CS"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 401)

    async def test_staff_can_crud_course(self):
        await self._login_admin()

        create_response = await self.async_client.post(
            "/api/courses/",
            data={"code": "CS101", "name": "Intro to CS"},
            content_type="application/json",
        )
        self.assertEqual(create_response.status_code, 201)
        course_id = _json(create_response)["id"]

        get_response = await self.async_client.get(f"/api/courses/{course_id}")
        self.assertEqual(get_response.status_code, 200)
        self.assertEqual(_json(get_response)["code"], "CS101")

        update_response = await self.async_client.patch(
            f"/api/courses/{course_id}", data={"name": "Intro to Computer Science"}, content_type="application/json"
        )
        self.assertEqual(update_response.status_code, 200)
        self.assertEqual(_json(update_response)["name"], "Intro to Computer Science")

        delete_response = await self.async_client.delete(f"/api/courses/{course_id}")
        self.assertEqual(delete_response.status_code, 200)
        self.assertFalse(await Course.objects.filter(id=course_id).aexists())

    async def test_duplicate_course_code_conflicts(self):
        await self._login_admin()
        await Course.objects.acreate(code="CS101", name="Intro to CS")
        response = await self.async_client.post(
            "/api/courses/", data={"code": "CS101", "name": "Other"}, content_type="application/json"
        )
        self.assertEqual(response.status_code, 409)

    async def test_assign_and_remove_staff(self):
        await self._login_admin()
        course = await Course.objects.acreate(code="CS101", name="Intro to CS")
        prof = await User.objects.acreate_user(username="prof", password="s3cret-pass")
        ta = await User.objects.acreate_user(username="ta", password="s3cret-pass")

        assign_response = await self.async_client.post(f"/api/courses/{course.id}/professors/{prof.id}")
        self.assertEqual(assign_response.status_code, 200)
        self.assertEqual([p["username"] for p in _json(assign_response)["professors"]], ["prof"])

        assign_ta_response = await self.async_client.post(f"/api/courses/{course.id}/tas/{ta.id}")
        self.assertEqual(assign_ta_response.status_code, 200)
        self.assertEqual([t["username"] for t in _json(assign_ta_response)["tas"]], ["ta"])

        remove_response = await self.async_client.delete(f"/api/courses/{course.id}/professors/{prof.id}")
        self.assertEqual(remove_response.status_code, 200)
        self.assertEqual(_json(remove_response)["professors"], [])

    async def test_same_code_allowed_in_different_semesters(self):
        await self._login_admin()
        await Course.objects.acreate(code="CS101", name="Intro to CS", semester="Fall 2026")

        again = await self.async_client.post(
            "/api/courses/",
            data={"code": "CS101", "name": "Intro to CS", "semester": "Spring 2027"},
            content_type="application/json",
        )
        self.assertEqual(again.status_code, 201)
        self.assertEqual(_json(again)["semester"], "Spring 2027")

        clash = await self.async_client.post(
            "/api/courses/",
            data={"code": "CS101", "name": "Intro to CS", "semester": "Fall 2026"},
            content_type="application/json",
        )
        self.assertEqual(clash.status_code, 409)

    async def test_student_roster_crud(self):
        await self._login_admin()
        course = await Course.objects.acreate(code="CS300", name="Rostered")

        created = await self.async_client.post(
            f"/api/courses/{course.id}/students",
            data={"student_id": "99001", "name": "Sam Student"},
            content_type="application/json",
        )
        self.assertEqual(created.status_code, 201)
        student_pk = _json(created)["id"]

        duplicate = await self.async_client.post(
            f"/api/courses/{course.id}/students",
            data={"student_id": "99001"},
            content_type="application/json",
        )
        self.assertEqual(duplicate.status_code, 409)

        renamed = await self.async_client.patch(
            f"/api/courses/{course.id}/students/{student_pk}",
            data={"name": "Samira Student"},
            content_type="application/json",
        )
        self.assertEqual(_json(renamed)["name"], "Samira Student")
        self.assertEqual(_json(renamed)["student_id"], "99001")

        listed = await self.async_client.get(f"/api/courses/{course.id}/students")
        self.assertEqual([s["student_id"] for s in _json(listed)], ["99001"])

        # a student of another course is not reachable through this one
        other = await Course.objects.acreate(code="CS301", name="Other")
        stranger = await Student.objects.acreate(course=other, student_id="99002")
        stray = await self.async_client.delete(f"/api/courses/{course.id}/students/{stranger.id}")
        self.assertEqual(stray.status_code, 404)

        removed = await self.async_client.delete(f"/api/courses/{course.id}/students/{student_pk}")
        self.assertEqual(removed.status_code, 200)
        self.assertFalse(await Student.objects.filter(pk=student_pk).aexists())


    async def test_group_types_are_independent_but_groups_within_one_are_not(self):
        await self._login_admin()
        course = await Course.objects.acreate(code="CS400", name="Grouped")
        one = await Student.objects.acreate(course=course, student_id="1")
        two = await Student.objects.acreate(course=course, student_id="2")

        bad = await self.async_client.post(
            f"/api/courses/{course.id}/group-types",
            data={"title": "Bad", "min_members": 3, "max_members": 2},
            content_type="application/json",
        )
        self.assertEqual(bad.status_code, 422)

        created = await self.async_client.post(
            f"/api/courses/{course.id}/group-types",
            data={"title": "Project", "description": "Term project", "min_members": 1, "max_members": 1},
            content_type="application/json",
        )
        self.assertEqual(created.status_code, 201)
        project = _json(created)["id"]

        duplicate = await self.async_client.post(
            f"/api/courses/{course.id}/group-types",
            data={"title": "Project"},
            content_type="application/json",
        )
        self.assertEqual(duplicate.status_code, 409)

        # groups of a type are numbered from 1
        await self.async_client.post(f"/api/courses/{course.id}/group-types/{project}/groups")
        added = await self.async_client.post(f"/api/courses/{course.id}/group-types/{project}/groups")
        self.assertEqual([g["number"] for g in _json(added)["groups"]], [1, 2])
        p1, p2 = (g["id"] for g in _json(added)["groups"])

        joined = await self.async_client.post(f"/api/courses/{course.id}/groups/{p1}/members/{one.id}")
        self.assertEqual([m["student_id"] for m in _json(joined)["groups"][0]["members"]], ["1"])

        full = await self.async_client.post(f"/api/courses/{course.id}/groups/{p1}/members/{two.id}")
        self.assertEqual(full.status_code, 409)

        # joining a sibling group of the same type leaves the first one
        moved = await self.async_client.post(f"/api/courses/{course.id}/groups/{p2}/members/{one.id}")
        self.assertEqual([[m["id"] for m in g["members"]] for g in _json(moved)["groups"]], [[], [one.id]])

        # a group of another type is joined on top, not instead
        lab = _json(
            await self.async_client.post(
                f"/api/courses/{course.id}/group-types",
                data={"title": "Lab", "max_members": 4},
                content_type="application/json",
            )
        )["id"]
        lab1 = _json(await self.async_client.post(f"/api/courses/{course.id}/group-types/{lab}/groups"))["groups"][0]["id"]
        await self.async_client.post(f"/api/courses/{course.id}/groups/{lab1}/members/{one.id}")
        self.assertEqual(await one.groups.acount(), 2)

        await self.async_client.post(f"/api/courses/{course.id}/groups/{lab1}/members/{two.id}")
        shrunk = await self.async_client.patch(
            f"/api/courses/{course.id}/group-types/{lab}",
            data={"max_members": 1},
            content_type="application/json",
        )
        self.assertEqual(shrunk.status_code, 409)

        left = await self.async_client.delete(f"/api/courses/{course.id}/groups/{lab1}/members/{one.id}")
        self.assertEqual([m["id"] for m in _json(left)["groups"][0]["members"]], [two.id])

        deleted = await self.async_client.delete(f"/api/courses/{course.id}/group-types/{project}")
        self.assertEqual(deleted.status_code, 200)
        self.assertEqual(await one.groups.acount(), 0)
