from uuid import UUID, uuid4

from django.db import IntegrityError
from ninja import Router
from ninja.errors import HttpError
from ninja.security import SessionAuth

from courses.models import Course
from courses.repository import CourseRepository, StudentRepository
from commons.crud import aget_or_404
from grading.repository import GradingComponentRepository, GradingSheetRepository, GradingTaskRepository
from grading.models import GradingComponent, GradingSheet, Score, SubGrade
from grading.schemas import (
    PublicSheetSchema,
    GradingComponentCreateSchema,
    GradingComponentSchema,
    GradingComponentUpdateSchema,
    GradingSheetCreateSchema,
    GradingSheetFullSchema,
    GradingSheetSchema,
    GradingSheetUpdateSchema,
    GradingTaskCreateSchema,
    GradingTaskSchema,
    ScoreBulkSchema,
    ScoreSchema,
    ScoreSetSchema,
    SubGradeCreateSchema,
    SubGradeSchema,
    SubGradeUpdateSchema,
)
from iam.models import User
from iam.repository import UserRepository
from iam.schemas import MessageSchema

session_auth = SessionAuth()

api = Router(tags=["grading"])


async def _get_course_or_404(course_id: int) -> Course:
    return await aget_or_404(CourseRepository.get_course(course_id), "Course not found")


async def _get_component_or_404(component_id: int):
    return await aget_or_404(GradingComponentRepository.get_component(component_id), "Grading component not found")


async def _require_professor_or_head_ta(course: Course, user: User) -> None:
    if not await CourseRepository.is_professor_or_head_ta(course, user):
        raise HttpError(403, "Only professors or head TAs of this course can do that")


@api.get("/courses/{course_id}/components", response=list[GradingComponentSchema], auth=session_auth)
async def list_components(request, course_id: int):
    await _get_course_or_404(course_id)
    return [component async for component in GradingComponentRepository.list_components(course_id)]


@api.post("/courses/{course_id}/components", response={201: GradingComponentSchema}, auth=session_auth)
async def create_component(request, course_id: int, payload: GradingComponentCreateSchema):
    course = await _get_course_or_404(course_id)
    await _require_professor_or_head_ta(course, request.auth)
    try:
        component = await GradingComponentRepository.create_component(course=course, **payload.dict())
    except IntegrityError:
        raise HttpError(409, "A grading component with that name already exists for this course")
    return 201, component


@api.patch("/components/{component_id}", response=GradingComponentSchema, auth=session_auth)
async def update_component(request, component_id: int, payload: GradingComponentUpdateSchema):
    component = await _get_component_or_404(component_id)
    await _require_professor_or_head_ta(component.course, request.auth)
    try:
        return await GradingComponentRepository.update_component(component, **payload.dict(exclude_unset=True))
    except IntegrityError:
        raise HttpError(409, "A grading component with that name already exists for this course")


@api.delete("/components/{component_id}", response=MessageSchema, auth=session_auth)
async def delete_component(request, component_id: int):
    component = await _get_component_or_404(component_id)
    await _require_professor_or_head_ta(component.course, request.auth)
    await GradingComponentRepository.delete_component(component)
    return {"detail": "Grading component deleted"}


@api.get("/components/{component_id}/tasks", response=list[GradingTaskSchema], auth=session_auth)
async def list_tasks(request, component_id: int):
    await _get_component_or_404(component_id)
    return [task async for task in GradingTaskRepository.list_tasks(component_id)]


@api.post("/components/{component_id}/tasks", response={201: GradingTaskSchema}, auth=session_auth)
async def create_task(request, component_id: int, payload: GradingTaskCreateSchema):
    component = await _get_component_or_404(component_id)
    course = component.course
    requester: User = request.auth
    await _require_professor_or_head_ta(course, requester)

    assignee = await aget_or_404(UserRepository.get_user(payload.assigned_to_id), "User not found")

    is_self = assignee.pk == requester.pk
    if not is_self and not await CourseRepository.is_ta(course, assignee):
        raise HttpError(403, "Grading tasks can only be assigned to yourself or a TA of this course")

    try:
        return 201, await GradingTaskRepository.create_task(
            component=component, assigned_to=assignee, assigned_by=requester
        )
    except IntegrityError:
        raise HttpError(409, "That user already has a grading task for this component")


@api.delete("/tasks/{task_id}", response=MessageSchema, auth=session_auth)
async def delete_task(request, task_id: int):
    task = await aget_or_404(GradingTaskRepository.get_task(task_id), "Grading task not found")
    await _require_professor_or_head_ta(task.component.course, request.auth)
    await GradingTaskRepository.delete_task(task)
    return {"detail": "Grading task deleted"}


# --- grading sheets ------------------------------------------------------


async def _get_sheet_or_404(sheet_id: int) -> GradingSheet:
    return await aget_or_404(GradingSheetRepository.get_sheet(sheet_id), "Grading sheet not found")


async def _get_subgrade_or_404(subgrade_id: int) -> SubGrade:
    return await aget_or_404(GradingSheetRepository.get_subgrade(subgrade_id), "Sub-grade not found")


async def _require_instructor(course: Course, user: User) -> None:
    if not await CourseRepository.is_instructor(course, user):
        raise HttpError(403, "Only professors or head TAs of this course can do that")


async def _can_enter_scores(component: GradingComponent, user: User) -> bool:
    """Professors and head TAs always; a TA only for components they were assigned."""
    if await CourseRepository.is_professor_or_head_ta(component.course, user):
        return True
    return await GradingSheetRepository.has_task(component.pk, user)


async def _require_score_access(component: GradingComponent, user: User) -> None:
    if not await _can_enter_scores(component, user):
        raise HttpError(403, "You have no grading task for this component")


@api.get("/components/{component_id}/sheet", response=GradingSheetSchema, auth=session_auth)
async def get_sheet(request, component_id: int):
    await _get_component_or_404(component_id)
    return await aget_or_404(
        GradingSheetRepository.get_sheet_for_component(component_id), "Grading sheet not found"
    )


@api.post("/components/{component_id}/sheet", response={201: GradingSheetSchema}, auth=session_auth)
async def create_sheet(request, component_id: int, payload: GradingSheetCreateSchema):
    component = await _get_component_or_404(component_id)
    await _require_professor_or_head_ta(component.course, request.auth)
    # Checked up front rather than caught: an IntegrityError inside the request's
    # transaction would poison it for every query after this one.
    if await GradingSheet.objects.filter(component=component).aexists():
        raise HttpError(409, "This component already has a grading sheet")
    return 201, await GradingSheetRepository.create_sheet(component=component, title=payload.title)


@api.patch("/sheets/{sheet_id}", response=GradingSheetSchema, auth=session_auth)
async def update_sheet(request, sheet_id: int, payload: GradingSheetUpdateSchema):
    sheet = await _get_sheet_or_404(sheet_id)
    await _require_professor_or_head_ta(sheet.component.course, request.auth)
    fields = payload.dict(exclude_unset=True)
    public = fields.pop("public", None)
    if public is not None:
        # a fresh token would break links already handed out, so keep the one we have
        await GradingSheetRepository.set_public_token(sheet, (sheet.public_token or uuid4()) if public else None)
    return await GradingSheetRepository.update_sheet(sheet, **fields)


@api.delete("/sheets/{sheet_id}", response=MessageSchema, auth=session_auth)
async def delete_sheet(request, sheet_id: int):
    sheet = await _get_sheet_or_404(sheet_id)
    await _require_professor_or_head_ta(sheet.component.course, request.auth)
    await GradingSheetRepository.delete_sheet(sheet)
    return {"detail": "Grading sheet deleted"}


@api.get("/sheets/{sheet_id}/full", response=GradingSheetFullSchema, auth=session_auth)
async def get_sheet_full(request, sheet_id: int):
    sheet = await _get_sheet_or_404(sheet_id)
    course = await _get_course_or_404(sheet.component.course_id)
    return {
        "sheet": sheet,
        "subgrades": [s async for s in GradingSheetRepository.list_subgrades(sheet_id)],
        "students": [s async for s in StudentRepository.list_students(course.pk)],
        "scores": [s async for s in GradingSheetRepository.list_scores(sheet_id)],
        "can_edit": await _can_enter_scores(sheet.component, request.auth),
    }


@api.post("/sheets/{sheet_id}/subgrades", response={201: SubGradeSchema}, auth=session_auth)
async def create_subgrade(request, sheet_id: int, payload: SubGradeCreateSchema):
    sheet = await _get_sheet_or_404(sheet_id)
    await _require_instructor(sheet.component.course, request.auth)
    if await SubGrade.objects.filter(sheet=sheet, name=payload.name).aexists():
        raise HttpError(409, "A sub-grade with that name already exists on this sheet")
    return 201, await GradingSheetRepository.create_subgrade(sheet=sheet, **payload.dict())


@api.patch("/subgrades/{subgrade_id}", response=SubGradeSchema, auth=session_auth)
async def update_subgrade(request, subgrade_id: int, payload: SubGradeUpdateSchema):
    subgrade = await _get_subgrade_or_404(subgrade_id)
    await _require_instructor(subgrade.sheet.component.course, request.auth)
    if payload.name and await SubGrade.objects.filter(sheet_id=subgrade.sheet_id, name=payload.name).exclude(
        pk=subgrade.pk
    ).aexists():
        raise HttpError(409, "A sub-grade with that name already exists on this sheet")
    return await GradingSheetRepository.update_subgrade(subgrade, **payload.dict(exclude_unset=True))


@api.delete("/subgrades/{subgrade_id}", response=MessageSchema, auth=session_auth)
async def delete_subgrade(request, subgrade_id: int):
    subgrade = await _get_subgrade_or_404(subgrade_id)
    await _require_instructor(subgrade.sheet.component.course, request.auth)
    await GradingSheetRepository.delete_subgrade(subgrade)
    return {"detail": "Sub-grade deleted"}


@api.put("/subgrades/{subgrade_id}/scores/{student_id}", response=ScoreSchema, auth=session_auth)
async def set_score(request, subgrade_id: int, student_id: int, payload: ScoreSetSchema):
    subgrade = await _get_subgrade_or_404(subgrade_id)
    component = subgrade.sheet.component
    await _require_score_access(component, request.auth)

    student = await aget_or_404(StudentRepository.get_student(student_id), "Student not found")
    if student.course_id != component.course_id:
        raise HttpError(400, "That student is not enrolled in this course")
    if payload.value is not None and not (0 <= payload.value <= float(subgrade.max_score)):
        raise HttpError(400, f"Score must be between 0 and {subgrade.max_score}")

    return await GradingSheetRepository.set_score(
        subgrade=subgrade, student=student, graded_by=request.auth, **payload.dict(exclude_unset=True)
    )


@api.put("/sheets/{sheet_id}/scores", response=list[ScoreSchema], auth=session_auth)
async def set_scores(request, sheet_id: int, payload: ScoreBulkSchema):
    """Bulk upsert for pasting a block of cells into the sheet."""
    sheet = await _get_sheet_or_404(sheet_id)
    await _require_score_access(sheet.component, request.auth)

    subgrades = {s.pk: s async for s in GradingSheetRepository.list_subgrades(sheet_id)}
    students = {s.pk: s async for s in StudentRepository.list_students(sheet.component.course_id)}

    saved = []
    for entry in payload.scores:
        subgrade = subgrades.get(entry.subgrade)
        student = students.get(entry.student)
        if subgrade is None:
            raise HttpError(400, "Sub-grade does not belong to this sheet")
        if student is None:
            raise HttpError(400, "That student is not enrolled in this course")
        if entry.value is not None and not (0 <= entry.value <= float(subgrade.max_score)):
            raise HttpError(400, f"Score for {subgrade.name} must be between 0 and {subgrade.max_score}")
        saved.append(
            await GradingSheetRepository.set_score(
                subgrade=subgrade,
                student=student,
                graded_by=request.auth,
                **entry.dict(exclude_unset=True, exclude={"subgrade", "student"}),
            )
        )
    return saved


# --- the published sheet: no session, guarded by an unguessable token ---


@api.get("/public/sheets/{token}", response=PublicSheetSchema)
def public_sheet(request, token: UUID):
    """Scores by student ID. Names and comments stay behind the login."""
    sheet = (
        GradingSheet.objects.select_related("component__course").filter(public_token=token).first()
    )
    if sheet is None:
        raise HttpError(404, "This sheet is not published")

    subgrades = list(sheet.subgrades.all())
    scores = {
        (score.student_id, score.subgrade_id): score
        for score in Score.objects.filter(subgrade__sheet=sheet)
    }
    rows = []
    for student in sheet.component.course.students.all():
        cells = [scores.get((student.id, subgrade.id)) for subgrade in subgrades]
        given = [cell.value for cell in cells if cell is not None and cell.value is not None]
        rows.append(
            {
                "student_id": student.student_id,
                "cells": [
                    {"value": cell.value, "comment": cell.comment} if cell else {}
                    for cell in cells
                ],
                "total": sum(given) if given else None,
            }
        )
    return {
        "course": str(sheet.component.course),
        "component": sheet.component.name,
        "title": sheet.title,
        "subgrades": [subgrade.name for subgrade in subgrades],
        "max_scores": [subgrade.max_score for subgrade in subgrades],
        "rows": rows,
    }
