import json

from django.test import TestCase

from courses.models import Course, Student
from grading.models import GradingComponent, GradingSheet, GradingTask, SubGrade, Score
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
            f"/api/grading/components/{component.id}/sheets",
            data={"title": "Midterm sheet"},
            content_type="application/json",
        )
        self.assertEqual(created.status_code, 201)
        sheet_id = _json(created)["id"]

        # one sheet per component
        # a second sheet is fine - q1, q2, q3 of one homework - but not the same title twice
        second = await self.async_client.post(
            f"/api/grading/components/{component.id}/sheets",
            data={"title": "q2"},
            content_type="application/json",
        )
        self.assertEqual(second.status_code, 201)
        duplicate = await self.async_client.post(
            f"/api/grading/components/{component.id}/sheets",
            data={"title": "q2"},
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

        commented = await self.async_client.put(
            f"/api/grading/subgrades/{subgrade_id}/scores/{student.id}",
            data={"value": 7.5, "comment": "half marks"},
            content_type="application/json",
        )
        self.assertEqual(commented.status_code, 200)

        # publishing hands out a read-only copy, and unpublishing takes it back
        published = await self.async_client.patch(
            f"/api/grading/sheets/{sheet_id}",
            data={"public": True},
            content_type="application/json",
        )
        token = _json(published)["public_token"]
        self.assertIsNotNone(token)

        await self.async_client.post("/api/iam/auth/logout")
        public = await self.async_client.get(f"/api/grading/public/sheets/{token}")
        body = _json(public)
        self.assertEqual(body["subgrades"], ["Q1"])
        self.assertEqual(
            body["rows"],
            [{"student_id": "99001", "cells": [{"value": 7.5, "comment": "half marks"}], "total": 7.5}],
        )
        self.assertNotIn("name", str(body))

        await self._login("sheet-prof")
        await self.async_client.patch(
            f"/api/grading/sheets/{sheet_id}",
            data={"public": False},
            content_type="application/json",
        )
        await self.async_client.post("/api/iam/auth/logout")
        self.assertEqual(
            (await self.async_client.get(f"/api/grading/public/sheets/{token}")).status_code, 404
        )

        await self._login("sheet-prof")
        deleted = await self.async_client.delete(f"/api/grading/sheets/{sheet_id}")
        self.assertEqual(deleted.status_code, 200)
        self.assertEqual(await GradingSheet.objects.filter(component=component).acount(), 1)

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

    async def test_subgrade_scoped_task_and_course_summary(self):
        course, prof, ta, other_ta, student, component = await self._setup()
        sheet = await GradingSheet.objects.acreate(component=component, title="HW1 sheet")
        q1 = await SubGrade.objects.acreate(sheet=sheet, name="q1", max_score=10)
        q2 = await SubGrade.objects.acreate(sheet=sheet, name="q2", max_score=10)

        await self._login("sheet-prof")
        scoped = await self.async_client.post(
            f"/api/grading/components/{component.id}/tasks",
            data={"assigned_to_id": ta.id, "subgrade_id": q1.id},
            content_type="application/json",
        )
        self.assertEqual(scoped.status_code, 201)

        # q1 is theirs, q2 is not
        await self._login("sheet-ta")
        mine = await self.async_client.put(
            f"/api/grading/subgrades/{q1.id}/scores/{student.id}",
            data={"value": 8},
            content_type="application/json",
        )
        self.assertEqual(mine.status_code, 200)
        theirs = await self.async_client.put(
            f"/api/grading/subgrades/{q2.id}/scores/{student.id}",
            data={"value": 8},
            content_type="application/json",
        )
        self.assertEqual(theirs.status_code, 403)
        full = _json(await self.async_client.get(f"/api/grading/sheets/{sheet.id}/full"))
        self.assertEqual(full["editable_subgrades"], [q1.id])

        await self._login("sheet-prof")
        await self.async_client.put(
            f"/api/grading/subgrades/{q2.id}/scores/{student.id}",
            data={"value": 6},
            content_type="application/json",
        )

        summary = _json(await self.async_client.get(f"/api/grading/courses/{course.id}/summary"))
        self.assertEqual([c["name"] for c in summary["components"]], [component.name])
        self.assertEqual(summary["rows"][0]["totals"], [14.0])
        # 14 of 20 is 70% of the only weighted component
        self.assertEqual(summary["rows"][0]["grade"], 70.0)

        published = _json(
            await self.async_client.patch(
                f"/api/grading/courses/{course.id}/summary",
                data={"public": True},
                content_type="application/json",
            )
        )
        token = published["summary_token"]
        await self.async_client.post("/api/iam/auth/logout")
        public = _json(await self.async_client.get(f"/api/grading/public/summaries/{token}"))
        self.assertEqual(public["rows"][0]["grade"], 70.0)
        self.assertEqual(public["rows"][0]["name"], "")

    async def test_component_sums_its_sheets(self):
        course, prof, ta, other_ta, student, component = await self._setup()
        for title, value in (("q1", 8), ("q2", 6)):
            sheet = await GradingSheet.objects.acreate(component=component, title=title)
            subgrade = await SubGrade.objects.acreate(sheet=sheet, name="part", max_score=10)
            await Score.objects.acreate(subgrade=subgrade, student=student, value=value)

        await self._login("sheet-prof")
        summary = _json(await self.async_client.get(f"/api/grading/components/{component.id}/summary"))
        self.assertEqual([sheet["title"] for sheet in summary["sheets"]], ["q1", "q2"])
        self.assertEqual([sheet["subgrades"][0]["name"] for sheet in summary["sheets"]], ["part", "part"])
        row = summary["rows"][0]
        self.assertEqual([cell["value"] for cell in row["cells"]], [8.0, 6.0])
        self.assertEqual(row["sheet_totals"], [8.0, 6.0])
        self.assertEqual(row["total"], 14.0)

        # the combined grid can be published, and then hides the names
        published = _json(
            await self.async_client.patch(
                f"/api/grading/components/{component.id}",
                data={"public": True},
                content_type="application/json",
            )
        )
        token = published["public_token"]
        self.assertIsNotNone(token)
        await self.async_client.post("/api/iam/auth/logout")
        public = _json(await self.async_client.get(f"/api/grading/public/components/{token}"))
        self.assertEqual(public["rows"][0]["total"], 14.0)
        self.assertEqual(public["rows"][0]["name"], "")
        await self._login("sheet-prof")
        await self.async_client.patch(
            f"/api/grading/components/{component.id}",
            data={"public": False},
            content_type="application/json",
        )
        closed = await self.async_client.get(f"/api/grading/public/components/{token}")
        self.assertEqual(closed.status_code, 404)

        # the course roll-up sees the component as one 14 out of 20
        course_summary = _json(await self.async_client.get(f"/api/grading/courses/{course.id}/summary"))
        self.assertEqual(course_summary["rows"][0]["totals"], [14.0])
        self.assertEqual(course_summary["rows"][0]["grade"], 70.0)
