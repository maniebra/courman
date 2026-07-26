import json

from django.test import TestCase

from courses.models import Course, Student
from grading.models import GradingComponent, GradingSheet, GradingTask, SubGrade
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


class GradingSheetTests(TestCase):
    async def _login(self, username):
        await self.async_client.post(
            "/api/iam/auth/login",
            data={"username": username, "password": "s3cret-pass"},
            content_type="application/json",
        )

    async def _setup(self):
        course = await Course.objects.acreate(code="CS200", name="Algorithms")
        prof = await User.objects.acreate_user(username="sheet-prof", password="s3cret-pass")
        ta = await User.objects.acreate_user(username="sheet-ta", password="s3cret-pass")
        other_ta = await User.objects.acreate_user(username="sheet-ta2", password="s3cret-pass")
        student = await Student.objects.acreate(course=course, student_id="99001", name="Sam Student")
        await course.professors.aadd(prof)
        await course.tas.aadd(ta)
        await course.tas.aadd(other_ta)
        component = await GradingComponent.objects.acreate(course=course, name="Midterm", weight=30)
        return course, prof, ta, other_ta, student, component

    async def test_sheet_lifecycle_and_scoring(self):
        course, prof, ta, other_ta, student, component = await self._setup()
        await self._login("sheet-prof")

        created = await self.async_client.post(
            f"/api/grading/components/{component.id}/sheet",
            data={"title": "Midterm sheet"},
            content_type="application/json",
        )
        self.assertEqual(created.status_code, 201)
        sheet_id = _json(created)["id"]

        # one sheet per component
        duplicate = await self.async_client.post(
            f"/api/grading/components/{component.id}/sheet",
            data={"title": "Again"},
            content_type="application/json",
        )
        self.assertEqual(duplicate.status_code, 409)

        subgrade = await self.async_client.post(
            f"/api/grading/sheets/{sheet_id}/subgrades",
            data={"name": "Q1", "max_score": 10},
            content_type="application/json",
        )
        self.assertEqual(subgrade.status_code, 201)
        subgrade_id = _json(subgrade)["id"]

        # out-of-range scores are rejected
        too_high = await self.async_client.put(
            f"/api/grading/subgrades/{subgrade_id}/scores/{student.id}",
            data={"value": 11},
            content_type="application/json",
        )
        self.assertEqual(too_high.status_code, 400)

        scored = await self.async_client.put(
            f"/api/grading/subgrades/{subgrade_id}/scores/{student.id}",
            data={"value": 7.5},
            content_type="application/json",
        )
        self.assertEqual(scored.status_code, 200)
        self.assertEqual(float(_json(scored)["value"]), 7.5)

        full = await self.async_client.get(f"/api/grading/sheets/{sheet_id}/full")
        body = _json(full)
        self.assertTrue(body["can_edit"])
        self.assertEqual([s["student_id"] for s in body["students"]], ["99001"])
        self.assertEqual(len(body["subgrades"]), 1)
        self.assertEqual(len(body["scores"]), 1)

        deleted = await self.async_client.delete(f"/api/grading/sheets/{sheet_id}")
        self.assertEqual(deleted.status_code, 200)
        self.assertFalse(await GradingComponent.objects.filter(sheet__isnull=False).aexists())

    async def test_only_assigned_ta_can_enter_scores(self):
        course, prof, ta, other_ta, student, component = await self._setup()
        sheet = await GradingSheet.objects.acreate(component=component, title="Midterm sheet")
        subgrade = await SubGrade.objects.acreate(sheet=sheet, name="Q1", max_score=10)
        await GradingTask.objects.acreate(component=component, assigned_to=ta, assigned_by=prof)

        await self._login("sheet-ta")
        allowed = await self.async_client.put(
            f"/api/grading/subgrades/{subgrade.id}/scores/{student.id}",
            data={"value": 5},
            content_type="application/json",
        )
        self.assertEqual(allowed.status_code, 200)

        # a TA on the course but without a task for this component stays out
        await self._login("sheet-ta2")
        refused = await self.async_client.put(
            f"/api/grading/subgrades/{subgrade.id}/scores/{student.id}",
            data={"value": 5},
            content_type="application/json",
        )
        self.assertEqual(refused.status_code, 403)

        # ...and cannot restructure the sheet either
        refused_subgrade = await self.async_client.post(
            f"/api/grading/sheets/{sheet.id}/subgrades",
            data={"name": "Q2", "max_score": 10},
            content_type="application/json",
        )
        self.assertEqual(refused_subgrade.status_code, 403)

    async def test_scores_are_limited_to_enrolled_students(self):
        course, prof, ta, other_ta, student, component = await self._setup()
        sheet = await GradingSheet.objects.acreate(component=component, title="Midterm sheet")
        subgrade = await SubGrade.objects.acreate(sheet=sheet, name="Q1", max_score=10)
        other_course = await Course.objects.acreate(code="CS999", name="Elsewhere")
        stranger = await Student.objects.acreate(course=other_course, student_id="99001")
        await self._login("sheet-prof")

        response = await self.async_client.put(
            f"/api/grading/subgrades/{subgrade.id}/scores/{stranger.id}",
            data={"value": 5},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)

    async def test_bulk_scores(self):
        course, prof, ta, other_ta, student, component = await self._setup()
        sheet = await GradingSheet.objects.acreate(component=component, title="Midterm sheet")
        q1 = await SubGrade.objects.acreate(sheet=sheet, name="Q1", max_score=10)
        q2 = await SubGrade.objects.acreate(sheet=sheet, name="Q2", max_score=10)
        await self._login("sheet-prof")

        response = await self.async_client.put(
            f"/api/grading/sheets/{sheet.id}/scores",
            data={
                "scores": [
                    {"subgrade": q1.id, "student": student.id, "value": 4},
                    {"subgrade": q2.id, "student": student.id, "value": 6},
                ]
            },
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual([float(s["value"]) for s in _json(response)], [4.0, 6.0])

        # a single bad cell rejects the whole paste
        rejected = await self.async_client.put(
            f"/api/grading/sheets/{sheet.id}/scores",
            data={"scores": [{"subgrade": q1.id, "student": student.id, "value": 99}]},
            content_type="application/json",
        )
        self.assertEqual(rejected.status_code, 400)

    async def test_comment_and_score_update_independently(self):
        course, prof, ta, other_ta, student, component = await self._setup()
        sheet = await GradingSheet.objects.acreate(component=component, title="Midterm sheet")
        q1 = await SubGrade.objects.acreate(sheet=sheet, name="Q1", max_score=10)
        await self._login("sheet-prof")
        url = f"/api/grading/subgrades/{q1.id}/scores/{student.id}"

        await self.async_client.put(url, data={"value": 6}, content_type="application/json")

        commented = await self.async_client.put(
            url, data={"comment": "missed the base case"}, content_type="application/json"
        )
        self.assertEqual(commented.status_code, 200)
        body = _json(commented)
        self.assertEqual(body["comment"], "missed the base case")
        self.assertEqual(float(body["value"]), 6.0)  # score untouched

        rescored = await self.async_client.put(url, data={"value": 7}, content_type="application/json")
        self.assertEqual(_json(rescored)["comment"], "missed the base case")  # comment untouched

    async def test_only_instructors_manage_subgrades(self):
        course, prof, ta, other_ta, student, component = await self._setup()
        sheet = await GradingSheet.objects.acreate(component=component, title="Midterm sheet")
        q1 = await SubGrade.objects.acreate(sheet=sheet, name="Q1", max_score=10)
        # a TA assigned to grade this component still may not change its structure
        await GradingTask.objects.acreate(component=component, assigned_to=ta, assigned_by=prof)
        await User.objects.acreate_superuser(username="root", password="s3cret-pass")

        for username in ("sheet-ta", "root"):
            await self._login(username)
            created = await self.async_client.post(
                f"/api/grading/sheets/{sheet.id}/subgrades",
                data={"name": f"Q-{username}", "max_score": 5},
                content_type="application/json",
            )
            self.assertEqual(created.status_code, 403, username)

            renamed = await self.async_client.patch(
                f"/api/grading/subgrades/{q1.id}",
                data={"name": "renamed"},
                content_type="application/json",
            )
            self.assertEqual(renamed.status_code, 403, username)

            removed = await self.async_client.delete(f"/api/grading/subgrades/{q1.id}")
            self.assertEqual(removed.status_code, 403, username)

        await self._login("sheet-prof")
        allowed = await self.async_client.post(
            f"/api/grading/sheets/{sheet.id}/subgrades",
            data={"name": "Q2", "max_score": 5},
            content_type="application/json",
        )
        self.assertEqual(allowed.status_code, 201)
