from ninja import Router
from ninja.errors import HttpError
from ninja.pagination import paginate
from ninja.security import SessionAuth

from commons.crud import ModelCrudView, aget_or_404
from courses.models import Course, Group, GroupType, Student
from courses.repository import CourseRepository, GroupRepository, StudentRepository
from iam.actions import Actions
from iam.permissions import HasAction
from courses.schemas import (
    CourseCreateSchema,
    CourseSchema,
    CourseUpdateSchema,
    GroupTypeCreateSchema,
    GroupTypeSchema,
    GroupTypeUpdateSchema,
    StudentCreateSchema,
    StudentSchema,
    StudentUpdateSchema,
)
from iam.repository import UserRepository
from iam.schemas import MessageSchema

session_auth = SessionAuth()
manage_courses = HasAction(Actions.COURSES_MANAGE)
manage_course_staff = HasAction(Actions.COURSE_STAFF_MANAGE)
manage_students = HasAction(Actions.STUDENTS_MANAGE)

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


@api.post("/", response={201: CourseCrud.schema}, auth=manage_courses)
async def create_course(request, payload: CourseCrud.create_schema):
    return 201, await course_crud.create(payload)


@api.patch("/{course_id}", response=CourseCrud.schema, auth=manage_courses)
async def update_course(request, course_id: int, payload: CourseCrud.update_schema):
    return await course_crud.update(course_id, payload)


@api.delete("/{course_id}", response=MessageSchema, auth=manage_courses)
async def delete_course(request, course_id: int):
    return await course_crud.destroy(course_id)


async def _get_course_and_user(course_id: int, user_id: int):
    course = await aget_or_404(CourseRepository.get_course(course_id), "Course not found")
    user = await aget_or_404(UserRepository.get_user(user_id), "User not found")
    return course, user


@api.post("/{course_id}/professors/{user_id}", response=CourseSchema, auth=manage_course_staff)
async def add_professor(request, course_id: int, user_id: int):
    course, user = await _get_course_and_user(course_id, user_id)
    await CourseRepository.add_professor(course, user)
    return await CourseRepository.get_course(course_id)


@api.delete("/{course_id}/professors/{user_id}", response=CourseSchema, auth=manage_course_staff)
async def remove_professor(request, course_id: int, user_id: int):
    course, user = await _get_course_and_user(course_id, user_id)
    await CourseRepository.remove_professor(course, user)
    return await CourseRepository.get_course(course_id)


@api.post("/{course_id}/head-tas/{user_id}", response=CourseSchema, auth=manage_course_staff)
async def add_head_ta(request, course_id: int, user_id: int):
    course, user = await _get_course_and_user(course_id, user_id)
    await CourseRepository.add_head_ta(course, user)
    return await CourseRepository.get_course(course_id)


@api.delete("/{course_id}/head-tas/{user_id}", response=CourseSchema, auth=manage_course_staff)
async def remove_head_ta(request, course_id: int, user_id: int):
    course, user = await _get_course_and_user(course_id, user_id)
    await CourseRepository.remove_head_ta(course, user)
    return await CourseRepository.get_course(course_id)


@api.post("/{course_id}/tas/{user_id}", response=CourseSchema, auth=manage_course_staff)
async def add_ta(request, course_id: int, user_id: int):
    course, user = await _get_course_and_user(course_id, user_id)
    await CourseRepository.add_ta(course, user)
    return await CourseRepository.get_course(course_id)


@api.delete("/{course_id}/tas/{user_id}", response=CourseSchema, auth=manage_course_staff)
async def remove_ta(request, course_id: int, user_id: int):
    course, user = await _get_course_and_user(course_id, user_id)
    await CourseRepository.remove_ta(course, user)
    return await CourseRepository.get_course(course_id)


async def _require_course_manager(course: Course, user) -> None:
    """Holding the action is not enough: it must be a course you actually run.

    Anyone with `courses.manage` (an administrator) runs all of them.
    """
    if user.is_superuser or await CourseRepository.has_action(user, Actions.COURSES_MANAGE):
        return
    if not await CourseRepository.is_professor_or_head_ta(course, user):
        raise HttpError(403, "Only administrators, professors or head TAs of this course can do that")


@api.get("/{course_id}/students", response=list[StudentSchema], auth=session_auth)
async def list_students(request, course_id: int):
    await aget_or_404(CourseRepository.get_course(course_id), "Course not found")
    return [student async for student in StudentRepository.list_students(course_id)]


@api.post("/{course_id}/students", response={201: StudentSchema}, auth=manage_students)
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


@api.patch("/{course_id}/students/{student_pk}", response=StudentSchema, auth=manage_students)
async def update_student(request, course_id: int, student_pk: int, payload: StudentUpdateSchema):
    student = await _get_student_or_404(course_id, student_pk)
    await _require_course_manager(student.course, request.auth)
    if payload.student_id and await Student.objects.filter(
        course_id=course_id, student_id=payload.student_id
    ).exclude(pk=student.pk).aexists():
        raise HttpError(409, "That student ID is already enrolled in this course")
    return await StudentRepository.update_student(student, **payload.dict(exclude_unset=True))


@api.delete("/{course_id}/students/{student_pk}", response=MessageSchema, auth=manage_students)
async def delete_student(request, course_id: int, student_pk: int):
    student = await _get_student_or_404(course_id, student_pk)
    await _require_course_manager(student.course, request.auth)
    await StudentRepository.delete_student(student)
    return {"detail": "Student removed from the course"}


def _check_sizes(minimum: int | None, maximum: int | None) -> None:
    if minimum is not None and minimum < 1:
        raise HttpError(422, "A group needs room for at least one member")
    if minimum is not None and maximum is not None and minimum > maximum:
        raise HttpError(422, "The minimum group size cannot exceed the maximum")


async def _get_type_or_404(course_id: int, type_pk: int) -> GroupType:
    group_type = await aget_or_404(GroupRepository.get_type(type_pk), "Group type not found")
    if group_type.course_id != course_id:
        raise HttpError(404, "Group type not found")
    return group_type


async def _get_group_or_404(course_id: int, group_pk: int) -> Group:
    group = await aget_or_404(GroupRepository.get_group(group_pk), "Group not found")
    if group.type.course_id != course_id:
        raise HttpError(404, "Group not found")
    return group


@api.get("/{course_id}/group-types", response=list[GroupTypeSchema], auth=session_auth)
async def list_group_types(request, course_id: int):
    await aget_or_404(CourseRepository.get_course(course_id), "Course not found")
    return [group_type async for group_type in GroupRepository.list_types(course_id)]


@api.post("/{course_id}/group-types", response={201: GroupTypeSchema}, auth=manage_students)
async def create_group_type(request, course_id: int, payload: GroupTypeCreateSchema):
    course = await aget_or_404(CourseRepository.get_course(course_id), "Course not found")
    await _require_course_manager(course, request.auth)
    _check_sizes(payload.min_members, payload.max_members)
    if await GroupType.objects.filter(course=course, title=payload.title).aexists():
        raise HttpError(409, "A group type with that title already exists in this course")
    return 201, await GroupRepository.create_type(course=course, **payload.dict())


@api.patch("/{course_id}/group-types/{type_pk}", response=GroupTypeSchema, auth=manage_students)
async def update_group_type(request, course_id: int, type_pk: int, payload: GroupTypeUpdateSchema):
    group_type = await _get_type_or_404(course_id, type_pk)
    await _require_course_manager(group_type.course, request.auth)
    fields = payload.dict(exclude_unset=True)
    _check_sizes(
        fields.get("min_members", group_type.min_members),
        fields.get("max_members", group_type.max_members),
    )
    if fields.get("max_members") is not None:
        fullest = max((len(group.members.all()) for group in group_type.groups.all()), default=0)
        if fields["max_members"] < fullest:
            raise HttpError(409, "A group of that type already has more members than that")
    if fields.get("title") and await GroupType.objects.filter(
        course_id=course_id, title=fields["title"]
    ).exclude(pk=group_type.pk).aexists():
        raise HttpError(409, "A group type with that title already exists in this course")
    return await GroupRepository.update_type(group_type, **fields)


@api.delete("/{course_id}/group-types/{type_pk}", response=MessageSchema, auth=manage_students)
async def delete_group_type(request, course_id: int, type_pk: int):
    group_type = await _get_type_or_404(course_id, type_pk)
    await _require_course_manager(group_type.course, request.auth)
    await GroupRepository.delete_type(group_type)
    return {"detail": "Group type deleted"}


@api.post("/{course_id}/group-types/{type_pk}/groups", response={201: GroupTypeSchema}, auth=manage_students)
async def add_group(request, course_id: int, type_pk: int):
    group_type = await _get_type_or_404(course_id, type_pk)
    await _require_course_manager(group_type.course, request.auth)
    await GroupRepository.add_group(group_type)
    return 201, await GroupRepository.get_type(type_pk)


@api.delete("/{course_id}/groups/{group_pk}", response=GroupTypeSchema, auth=manage_students)
async def delete_group(request, course_id: int, group_pk: int):
    group = await _get_group_or_404(course_id, group_pk)
    await _require_course_manager(group.type.course, request.auth)
    type_pk = group.type_id
    await GroupRepository.delete_group(group)
    return await GroupRepository.get_type(type_pk)


@api.post("/{course_id}/groups/{group_pk}/members/{student_pk}", response=GroupTypeSchema, auth=manage_students)
async def add_group_member(request, course_id: int, group_pk: int, student_pk: int):
    group = await _get_group_or_404(course_id, group_pk)
    await _require_course_manager(group.type.course, request.auth)
    student = await _get_student_or_404(course_id, student_pk)
    if (
        not await group.members.filter(pk=student.pk).aexists()
        and await GroupRepository.member_count(group) >= group.type.max_members
    ):
        raise HttpError(409, "That group is already full")
    await GroupRepository.join(student, group)
    return await GroupRepository.get_type(group.type_id)


@api.delete("/{course_id}/groups/{group_pk}/members/{student_pk}", response=GroupTypeSchema, auth=manage_students)
async def remove_group_member(request, course_id: int, group_pk: int, student_pk: int):
    group = await _get_group_or_404(course_id, group_pk)
    await _require_course_manager(group.type.course, request.auth)
    student = await _get_student_or_404(course_id, student_pk)
    await GroupRepository.leave(student, group)
    return await GroupRepository.get_type(group.type_id)
