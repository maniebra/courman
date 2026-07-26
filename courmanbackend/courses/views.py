from ninja import Router
from ninja.errors import HttpError
from ninja.pagination import paginate
from ninja.security import SessionAuth, SessionAuthIsStaff

from commons.crud import ModelCrudView, aget_or_404
from courses.models import Course, Student
from courses.repository import CourseRepository, StudentRepository
from courses.schemas import (
    CourseCreateSchema,
    CourseSchema,
    CourseUpdateSchema,
    StudentCreateSchema,
    StudentSchema,
    StudentUpdateSchema,
)
from iam.repository import UserRepository
from iam.schemas import MessageSchema

session_auth = SessionAuth()
staff_auth = SessionAuthIsStaff()

api = Router(tags=["courses"])


class CourseCrud(ModelCrudView[Course]):
    schema = CourseSchema
    create_schema = CourseCreateSchema
    update_schema = CourseUpdateSchema
    list_fn = staticmethod(CourseRepository.list_courses)
    get_fn = staticmethod(CourseRepository.get_course)
    create_fn = staticmethod(CourseRepository.create_course)
    update_fn = staticmethod(CourseRepository.update_course)
    delete_fn = staticmethod(CourseRepository.delete_course)
    not_found_message = "Course not found"
    conflict_message = "A course with that code already exists for that semester"
    deleted_message = "Course deleted"


course_crud = CourseCrud()


@api.get("/", response=list[CourseCrud.schema], auth=session_auth)
@paginate
async def list_courses(request):
    return course_crud.list()


@api.get("/{course_id}", response=CourseCrud.schema, auth=session_auth)
async def get_course(request, course_id: int):
    return await course_crud.retrieve(course_id)


@api.post("/", response={201: CourseCrud.schema}, auth=staff_auth)
async def create_course(request, payload: CourseCrud.create_schema):
    return 201, await course_crud.create(payload)


@api.patch("/{course_id}", response=CourseCrud.schema, auth=staff_auth)
async def update_course(request, course_id: int, payload: CourseCrud.update_schema):
    return await course_crud.update(course_id, payload)


@api.delete("/{course_id}", response=MessageSchema, auth=staff_auth)
async def delete_course(request, course_id: int):
    return await course_crud.destroy(course_id)


async def _get_course_and_user(course_id: int, user_id: int):
    course = await aget_or_404(CourseRepository.get_course(course_id), "Course not found")
    user = await aget_or_404(UserRepository.get_user(user_id), "User not found")
    return course, user


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


async def _require_course_manager(course: Course, user) -> None:
    """Staff run every course; professors and head TAs run their own."""
    if user.is_staff:
        return
    if not await CourseRepository.is_professor_or_head_ta(course, user):
        raise HttpError(403, "Only staff, professors or head TAs of this course can do that")


@api.get("/{course_id}/students", response=list[StudentSchema], auth=session_auth)
async def list_students(request, course_id: int):
    await aget_or_404(CourseRepository.get_course(course_id), "Course not found")
    return [student async for student in StudentRepository.list_students(course_id)]


@api.post("/{course_id}/students", response={201: StudentSchema}, auth=session_auth)
async def create_student(request, course_id: int, payload: StudentCreateSchema):
    course = await aget_or_404(CourseRepository.get_course(course_id), "Course not found")
    await _require_course_manager(course, request.auth)
    if await Student.objects.filter(course=course, student_id=payload.student_id).aexists():
        raise HttpError(409, "That student ID is already enrolled in this course")
    return 201, await StudentRepository.create_student(course=course, **payload.dict())


async def _get_student_or_404(course_id: int, student_pk: int) -> Student:
    student = await aget_or_404(StudentRepository.get_student(student_pk), "Student not found")
    if student.course_id != course_id:
        raise HttpError(404, "Student not found")
    return student


@api.patch("/{course_id}/students/{student_pk}", response=StudentSchema, auth=session_auth)
async def update_student(request, course_id: int, student_pk: int, payload: StudentUpdateSchema):
    student = await _get_student_or_404(course_id, student_pk)
    await _require_course_manager(student.course, request.auth)
    if payload.student_id and await Student.objects.filter(
        course_id=course_id, student_id=payload.student_id
    ).exclude(pk=student.pk).aexists():
        raise HttpError(409, "That student ID is already enrolled in this course")
    return await StudentRepository.update_student(student, **payload.dict(exclude_unset=True))


@api.delete("/{course_id}/students/{student_pk}", response=MessageSchema, auth=session_auth)
async def delete_student(request, course_id: int, student_pk: int):
    student = await _get_student_or_404(course_id, student_pk)
    await _require_course_manager(student.course, request.auth)
    await StudentRepository.delete_student(student)
    return {"detail": "Student removed from the course"}
