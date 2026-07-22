from django.db import IntegrityError
from ninja import Router
from ninja.errors import HttpError
from ninja.pagination import paginate
from ninja.security import SessionAuth, SessionAuthIsStaff

from courses.models import Course
from courses.repository import CourseRepository
from courses.schemas import CourseCreateSchema, CourseSchema, CourseUpdateSchema
from iam.models import User
from iam.repository import UserRepository
from iam.schemas import MessageSchema

session_auth = SessionAuth()
staff_auth = SessionAuthIsStaff()

api = Router(tags=["courses"])


async def _get_course_and_user(course_id: int, user_id: int) -> tuple[Course, User]:
    try:
        course = await CourseRepository.get_course(course_id)
    except Course.DoesNotExist:
        raise HttpError(404, "Course not found")
    try:
        user = await UserRepository.get_user(user_id)
    except User.DoesNotExist:
        raise HttpError(404, "User not found")
    return course, user


@api.get("/", response=list[CourseSchema], auth=session_auth)
@paginate
async def list_courses(request):
    return CourseRepository.list_courses()


@api.get("/{course_id}", response=CourseSchema, auth=session_auth)
async def get_course(request, course_id: int):
    try:
        return await CourseRepository.get_course(course_id)
    except Course.DoesNotExist:
        raise HttpError(404, "Course not found")


@api.post("/", response={201: CourseSchema}, auth=staff_auth)
async def create_course(request, payload: CourseCreateSchema):
    try:
        course = await CourseRepository.create_course(**payload.dict())
    except IntegrityError:
        raise HttpError(409, "A course with that code already exists")
    return 201, course


@api.patch("/{course_id}", response=CourseSchema, auth=staff_auth)
async def update_course(request, course_id: int, payload: CourseUpdateSchema):
    try:
        course = await CourseRepository.get_course(course_id)
    except Course.DoesNotExist:
        raise HttpError(404, "Course not found")
    try:
        return await CourseRepository.update_course(course, **payload.dict(exclude_unset=True))
    except IntegrityError:
        raise HttpError(409, "A course with that code already exists")


@api.delete("/{course_id}", response=MessageSchema, auth=staff_auth)
async def delete_course(request, course_id: int):
    try:
        course = await CourseRepository.get_course(course_id)
    except Course.DoesNotExist:
        raise HttpError(404, "Course not found")
    await CourseRepository.delete_course(course)
    return {"detail": "Course deleted"}


@api.post("/{course_id}/professors/{user_id}", response=CourseSchema, auth=staff_auth)
async def add_professor(request, course_id: int, user_id: int):
    course, user = await _get_course_and_user(course_id, user_id)
    await CourseRepository.add_professor(course, user)
    return await CourseRepository.get_course(course_id)


@api.delete("/{course_id}/professors/{user_id}", response=CourseSchema, auth=staff_auth)
async def remove_professor(request, course_id: int, user_id: int):
    course, user = await _get_course_and_user(course_id, user_id)
    await CourseRepository.remove_professor(course, user)
    return await CourseRepository.get_course(course_id)


@api.post("/{course_id}/head-tas/{user_id}", response=CourseSchema, auth=staff_auth)
async def add_head_ta(request, course_id: int, user_id: int):
    course, user = await _get_course_and_user(course_id, user_id)
    await CourseRepository.add_head_ta(course, user)
    return await CourseRepository.get_course(course_id)


@api.delete("/{course_id}/head-tas/{user_id}", response=CourseSchema, auth=staff_auth)
async def remove_head_ta(request, course_id: int, user_id: int):
    course, user = await _get_course_and_user(course_id, user_id)
    await CourseRepository.remove_head_ta(course, user)
    return await CourseRepository.get_course(course_id)


@api.post("/{course_id}/tas/{user_id}", response=CourseSchema, auth=staff_auth)
async def add_ta(request, course_id: int, user_id: int):
    course, user = await _get_course_and_user(course_id, user_id)
    await CourseRepository.add_ta(course, user)
    return await CourseRepository.get_course(course_id)


@api.delete("/{course_id}/tas/{user_id}", response=CourseSchema, auth=staff_auth)
async def remove_ta(request, course_id: int, user_id: int):
    course, user = await _get_course_and_user(course_id, user_id)
    await CourseRepository.remove_ta(course, user)
    return await CourseRepository.get_course(course_id)
