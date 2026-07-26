from django.db import IntegrityError
from ninja import Router
from ninja.errors import HttpError
from ninja.security import SessionAuth

from courses.models import Course
from courses.repository import CourseRepository
from commons.crud import aget_or_404
from grading.repository import GradingComponentRepository, GradingTaskRepository
from grading.schemas import (
    GradingComponentCreateSchema,
    GradingComponentSchema,
    GradingComponentUpdateSchema,
    GradingTaskCreateSchema,
    GradingTaskSchema,
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
