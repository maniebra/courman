import json

from django.test import TestCase

from courses.models import Course
from grading.models import GradingComponent, GradingTask
from iam.models import User


def _json(response):
    return json.loads(response.content)


class GradingComponentTests(TestCase):
    async def _login(self, username):
        await self.async_client.post(
            "/api/iam/auth/login",
            data={"username": username, "password": "s3cret-pass"},
            content_type="application/json",
        )

    async def _make_course_with_staff(self):
        course = await Course.objects.acreate(code="CS101", name="Intro to CS")
        prof = await User.objects.acreate_user(username="prof", password="s3cret-pass")
        head_ta = await User.objects.acreate_user(username="headta", password="s3cret-pass")
        ta = await User.objects.acreate_user(username="ta", password="s3cret-pass")
        outsider = await User.objects.acreate_user(username="outsider", password="s3cret-pass")
        await course.professors.aadd(prof)
        await course.head_tas.aadd(head_ta)
        await course.tas.aadd(ta)
        return course, prof, head_ta, ta, outsider

    async def test_professor_can_create_component(self):
        course, prof, *_ = await self._make_course_with_staff()
        await self._login("prof")

        response = await self.async_client.post(
            f"/api/grading/courses/{course.id}/components",
            data={"name": "Midterm", "weight": 30},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(_json(response)["name"], "Midterm")
        self.assertTrue(await GradingComponent.objects.filter(course=course, name="Midterm").aexists())

    async def test_outsider_cannot_create_component(self):
        course, *_ , outsider = await self._make_course_with_staff()
        await self._login("outsider")

        response = await self.async_client.post(
            f"/api/grading/courses/{course.id}/components",
            data={"name": "Midterm", "weight": 30},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 403)

    async def test_ta_cannot_create_component(self):
        course, *_ = await self._make_course_with_staff()
        await self._login("ta")

        response = await self.async_client.post(
            f"/api/grading/courses/{course.id}/components",
            data={"name": "Midterm", "weight": 30},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 403)


class GradingTaskAssignmentTests(TestCase):
    async def _login(self, username):
        await self.async_client.post(
            "/api/iam/auth/login",
            data={"username": username, "password": "s3cret-pass"},
            content_type="application/json",
        )

    async def _make_course_with_staff(self):
        course = await Course.objects.acreate(code="CS101", name="Intro to CS")
        prof = await User.objects.acreate_user(username="prof", password="s3cret-pass")
        head_ta = await User.objects.acreate_user(username="headta", password="s3cret-pass")
        ta = await User.objects.acreate_user(username="ta", password="s3cret-pass")
        outsider = await User.objects.acreate_user(username="outsider", password="s3cret-pass")
        await course.professors.aadd(prof)
        await course.head_tas.aadd(head_ta)
        await course.tas.aadd(ta)
        component = await GradingComponent.objects.acreate(course=course, name="Midterm", weight=30)
        return course, component, prof, head_ta, ta, outsider

    async def test_professor_can_assign_task_to_ta(self):
        course, component, prof, head_ta, ta, outsider = await self._make_course_with_staff()
        await self._login("prof")

        response = await self.async_client.post(
            f"/api/grading/components/{component.id}/tasks",
            data={"assigned_to_id": ta.id},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(_json(response)["assigned_to"]["username"], "ta")
        self.assertTrue(await GradingTask.objects.filter(component=component, assigned_to=ta).aexists())

    async def test_head_ta_can_assign_task_to_self(self):
        course, component, prof, head_ta, ta, outsider = await self._make_course_with_staff()
        await self._login("headta")

        response = await self.async_client.post(
            f"/api/grading/components/{component.id}/tasks",
            data={"assigned_to_id": head_ta.id},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(_json(response)["assigned_to"]["username"], "headta")

    async def test_cannot_assign_task_to_outsider(self):
        course, component, prof, head_ta, ta, outsider = await self._make_course_with_staff()
        await self._login("prof")

        response = await self.async_client.post(
            f"/api/grading/components/{component.id}/tasks",
            data={"assigned_to_id": outsider.id},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 403)

    async def test_ta_cannot_assign_tasks(self):
        course, component, prof, head_ta, ta, outsider = await self._make_course_with_staff()
        await self._login("ta")

        response = await self.async_client.post(
            f"/api/grading/components/{component.id}/tasks",
            data={"assigned_to_id": ta.id},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 403)

    async def test_professor_can_delete_task(self):
        course, component, prof, head_ta, ta, outsider = await self._make_course_with_staff()
        task = await GradingTask.objects.acreate(component=component, assigned_to=ta, assigned_by=prof)
        await self._login("prof")

        response = await self.async_client.delete(f"/api/grading/tasks/{task.id}")
        self.assertEqual(response.status_code, 200)
        self.assertFalse(await GradingTask.objects.filter(id=task.id).aexists())
