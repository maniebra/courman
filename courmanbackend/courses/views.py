from ninja import Router
from ninja.pagination import paginate
from ninja.security import SessionAuth, SessionAuthIsStaff

from commons.crud import ModelCrudView, aget_or_404
from courses.models import Course
from courses.repository import CourseRepository
from courses.schemas import CourseCreateSchema, CourseSchema, CourseUpdateSchema
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
    conflict_message = "A course with that code already exists"
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
