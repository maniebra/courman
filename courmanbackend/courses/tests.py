import json

from django.test import TestCase

from courses.models import Course, Student
from iam.models import User


def _json(response):
    return json.loads(response.content)


class CourseCrudTests(TestCase):
    async def _login_staff(self):
        await User.objects.acreate_user(username="admin", password="s3cret-pass", is_staff=True)
        await self.async_client.post(
            "/api/iam/auth/login",
            data={"username": "admin", "password": "s3cret-pass"},
            content_type="application/json",
        )

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
        await self._login_staff()

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
        await self._login_staff()
        await Course.objects.acreate(code="CS101", name="Intro to CS")
        response = await self.async_client.post(
            "/api/courses/", data={"code": "CS101", "name": "Other"}, content_type="application/json"
        )
        self.assertEqual(response.status_code, 409)

    async def test_assign_and_remove_staff(self):
        await self._login_staff()
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
        await self._login_staff()
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
        await self._login_staff()
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
