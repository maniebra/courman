from uuid import UUID, uuid4

from django.db import transaction
from django.db.models import Max
from ninja import Router
from ninja.errors import HttpError
from ninja.pagination import paginate
from ninja.security import SessionAuth
from ninja.throttling import AnonRateThrottle

from commons.crud import ModelCrudView, aget_or_404
from courses.models import Course, Group, GroupType, HandoffItem, Student
from courses.repository import CourseRepository, GroupRepository, HandoffRepository, StudentRepository
from iam.actions import Actions
from iam.permissions import HasAction
from courses.schemas import (
    CourseCreateSchema,
    CourseSchema,
    CourseUpdateSchema,
    GroupSignupFormSchema,
    GroupSignupSchema,
    GroupTypeCreateSchema,
    GroupTypeSchema,
    GroupTypeUpdateSchema,
    HandoffBookingSchema,
    HandoffFormSchema,
    HandoffItemCreateSchema,
    HandoffItemSchema,
    HandoffItemUpdateSchema,
    HandoffSlotCreateSchema,
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
    signup_open = fields.pop("signup_open", None)
    if signup_open is not None:
        # a fresh token would break links already handed out, so keep the one we have
        await GroupRepository.set_signup_token(
            group_type, (group_type.signup_token or uuid4()) if signup_open else None
        )
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


# --- public sign-up form: no session, guarded by an unguessable token ---


def _open_signup_or_404(token: UUID) -> GroupType:
    try:
        return GroupType.objects.select_related("course").get(signup_token=token)
    except GroupType.DoesNotExist:
        raise HttpError(404, "This sign-up form is closed or does not exist")


@api.get("/public/group-signups/{token}", response=GroupSignupFormSchema)
def group_signup_form(request, token: UUID):
    group_type = _open_signup_or_404(token)
    return {
        "course": str(group_type.course),
        "title": group_type.title,
        "description": group_type.description,
        "min_members": group_type.min_members,
        "max_members": group_type.max_members,
    }


@api.post(
    "/public/group-signups/{token}",
    response={201: MessageSchema},
    throttle=[AnonRateThrottle("20/h")],
)
@transaction.atomic
def group_signup(request, token: UUID, payload: GroupSignupSchema):
    """Anyone with the link may form a group, but only out of real student IDs.

    The type row is locked for the duration: the group number is `max + 1`, and
    two submissions arriving together must not both claim it.
    """
    group_type = GroupType.objects.select_for_update().select_related("course").filter(signup_token=token).first()
    if group_type is None:
        raise HttpError(404, "This sign-up form is closed or does not exist")

    student_ids = list(dict.fromkeys(sid.strip() for sid in payload.student_ids if sid.strip()))
    if not group_type.min_members <= len(student_ids) <= group_type.max_members:
        raise HttpError(
            422,
            f"A {group_type.title} group needs between {group_type.min_members} "
            f"and {group_type.max_members} student IDs",
        )

    students = list(Student.objects.filter(course_id=group_type.course_id, student_id__in=student_ids))
    unknown = sorted(set(student_ids) - {student.student_id for student in students})
    if unknown:
        raise HttpError(422, f"Not enrolled in {group_type.course.code}: {', '.join(unknown)}")

    taken = sorted(
        student.student_id for student in students if student.groups.filter(type=group_type).exists()
    )
    if taken:
        raise HttpError(409, f"Already in a {group_type.title} group: {', '.join(taken)}")

    number = (group_type.groups.aggregate(highest=Max("number"))["highest"] or 0) + 1
    group = Group.objects.create(type=group_type, number=number)
    group.members.set(students)
    return 201, {"detail": f"Signed up as {group_type.title} {number}"}


# --- handoff sessions: TAs offer slots, groups book one ---


async def _is_course_staff(course: Course, user) -> bool:
    return await CourseRepository.is_instructor(course, user) or await CourseRepository.is_ta(course, user)


async def _require_course_staff(course: Course, user) -> None:
    """TAs run handoffs too, so this is wider than `_require_course_manager`."""
    if user.is_superuser or await CourseRepository.has_action(user, Actions.COURSES_MANAGE):
        return
    if not await _is_course_staff(course, user):
        raise HttpError(403, "Only the staff of this course can do that")


async def _get_item_or_404(course_id: int, item_pk: int) -> HandoffItem:
    item = await aget_or_404(HandoffRepository.get_item(item_pk), "Handoff not found")
    if item.course_id != course_id:
        raise HttpError(404, "Handoff not found")
    return item


@api.get("/{course_id}/handoffs", response=list[HandoffItemSchema], auth=session_auth)
async def list_handoffs(request, course_id: int):
    await aget_or_404(CourseRepository.get_course(course_id), "Course not found")
    return [item async for item in HandoffRepository.list_items(course_id)]


@api.post("/{course_id}/handoffs", response={201: HandoffItemSchema}, auth=manage_students)
async def create_handoff(request, course_id: int, payload: HandoffItemCreateSchema):
    course = await aget_or_404(CourseRepository.get_course(course_id), "Course not found")
    await _require_course_manager(course, request.auth)
    group_type = await _get_type_or_404(course_id, payload.group_type)
    if payload.slot_minutes < 1:
        raise HttpError(422, "A slot has to be at least a minute long")
    if await HandoffItem.objects.filter(course=course, title=payload.title).aexists():
        raise HttpError(409, "A handoff with that title already exists in this course")
    return 201, await HandoffRepository.create_item(
        course=course,
        group_type=group_type,
        title=payload.title,
        description=payload.description,
        hide_ta=payload.hide_ta,
        slot_minutes=payload.slot_minutes,
        break_minutes=payload.break_minutes,
    )


@api.patch("/{course_id}/handoffs/{item_pk}", response=HandoffItemSchema, auth=manage_students)
async def update_handoff(request, course_id: int, item_pk: int, payload: HandoffItemUpdateSchema):
    item = await _get_item_or_404(course_id, item_pk)
    await _require_course_manager(item.course, request.auth)
    fields = payload.dict(exclude_unset=True)
    signup_open = fields.pop("signup_open", None)
    if signup_open is not None:
        await HandoffRepository.set_signup_token(item, (item.signup_token or uuid4()) if signup_open else None)
    if fields.get("slot_minutes") is not None and fields["slot_minutes"] < 1:
        raise HttpError(422, "A slot has to be at least a minute long")
    if fields.get("title") and await HandoffItem.objects.filter(
        course_id=course_id, title=fields["title"]
    ).exclude(pk=item.pk).aexists():
        raise HttpError(409, "A handoff with that title already exists in this course")
    return await HandoffRepository.update_item(item, **fields)


@api.delete("/{course_id}/handoffs/{item_pk}", response=MessageSchema, auth=manage_students)
async def delete_handoff(request, course_id: int, item_pk: int):
    item = await _get_item_or_404(course_id, item_pk)
    await _require_course_manager(item.course, request.auth)
    await HandoffRepository.delete_item(item)
    return {"detail": "Handoff deleted"}


@api.post("/{course_id}/handoffs/{item_pk}/slots", response={201: HandoffItemSchema}, auth=session_auth)
async def add_handoff_slot(request, course_id: int, item_pk: int, payload: HandoffSlotCreateSchema):
    """A TA offers their own windows; whoever runs the course may offer one for any TA.

    The window is cut into `slot_minutes` slots with `break_minutes` between them.
    """
    item = await _get_item_or_404(course_id, item_pk)
    await _require_course_staff(item.course, request.auth)
    if payload.end <= payload.start:
        raise HttpError(422, "A slot has to end after it starts")
    ta = request.auth
    if payload.ta is not None and payload.ta != request.auth.pk:
        await _require_course_manager(item.course, request.auth)
        ta = await aget_or_404(UserRepository.get_user(payload.ta), "User not found")
        if not await _is_course_staff(item.course, ta):
            raise HttpError(422, "That user is not on this course's staff")
    if not await HandoffRepository.add_slots(item=item, ta=ta, start=payload.start, end=payload.end):
        raise HttpError(422, f"That window is shorter than one {item.slot_minutes} minute slot, or is already offered")
    return 201, await HandoffRepository.get_item(item_pk)


@api.delete("/{course_id}/handoff-slots/{slot_pk}", response=HandoffItemSchema, auth=session_auth)
async def delete_handoff_slot(request, course_id: int, slot_pk: int):
    slot = await aget_or_404(HandoffRepository.get_slot(slot_pk), "Slot not found")
    if slot.item.course_id != course_id:
        raise HttpError(404, "Slot not found")
    await _require_course_staff(slot.item.course, request.auth)
    # your own slots are yours to withdraw; taking someone else's off the board
    # is a call for whoever runs the course
    if slot.ta_id != request.auth.pk:
        await _require_course_manager(slot.item.course, request.auth)
    await HandoffRepository.delete_slot(slot)
    return await HandoffRepository.get_item(slot.item_id)


@api.delete("/{course_id}/handoff-slots/{slot_pk}/booking", response=HandoffItemSchema, auth=session_auth)
async def clear_handoff_booking(request, course_id: int, slot_pk: int):
    """Cancelling someone's booking is a professor/head TA call, not the slot owner's."""
    slot = await aget_or_404(HandoffRepository.get_slot(slot_pk), "Slot not found")
    if slot.item.course_id != course_id:
        raise HttpError(404, "Slot not found")
    await _require_course_manager(slot.item.course, request.auth)
    await HandoffRepository.clear_booking(slot)
    return await HandoffRepository.get_item(slot.item_id)


# --- public booking form ---


def _handoff_form(item: HandoffItem) -> dict:
    return {
        "course": str(item.course),
        "title": item.title,
        "description": item.description,
        "group_type": item.group_type.title,
        "slots": [
            {
                "id": slot.id,
                "start": slot.start,
                "end": slot.end,
                # the students see a time, not a person, unless the staff say otherwise
                "ta": "" if item.hide_ta else (slot.ta.get_full_name() or slot.ta.username),
                "taken": slot.group_id is not None,
            }
            for slot in item.slots.all()
        ],
    }


@api.get("/public/handoff-forms/{token}", response=HandoffFormSchema)
def handoff_form(request, token: UUID):
    item = (
        HandoffItem.objects.select_related("course", "group_type")
        .prefetch_related("slots__ta")
        .filter(signup_token=token)
        .first()
    )
    if item is None:
        raise HttpError(404, "This booking form is closed or does not exist")
    return _handoff_form(item)


@api.post("/public/handoff-forms/{token}", response={201: MessageSchema}, throttle=[AnonRateThrottle("20/h")])
@transaction.atomic
def book_handoff(request, token: UUID, payload: HandoffBookingSchema):
    """Whoever books must be in the group, and must say the others agreed to the time."""
    item = (
        HandoffItem.objects.select_for_update()
        .select_related("course", "group_type")
        .filter(signup_token=token)
        .first()
    )
    if item is None:
        raise HttpError(404, "This booking form is closed or does not exist")
    if not payload.teammates_confirmed:
        raise HttpError(422, "Confirm that your teammates agreed to this time")

    student = Student.objects.filter(
        course_id=item.course_id, student_id=payload.student_id.strip()
    ).first()
    if student is None:
        raise HttpError(422, f"Not enrolled in {item.course.code}: {payload.student_id}")

    group = Group.objects.filter(type=item.group_type, members=student).first()
    if group is None:
        raise HttpError(422, f"You are not in a {item.group_type.title} group yet")

    slot = item.slots.filter(pk=payload.slot_id).first()
    if slot is None:
        raise HttpError(404, "Slot not found")
    if slot.group_id is not None:
        raise HttpError(409, "That slot has just been taken")

    booked = item.slots.filter(group=group).first()
    if booked is not None:
        raise HttpError(409, f"{item.group_type.title} {group.number} already booked {booked.start:%Y-%m-%d %H:%M}")

    slot.group = group
    slot.booked_by = student
    slot.teammates_confirmed = True
    slot.save(update_fields=["group", "booked_by", "teammates_confirmed"])
    return 201, {"detail": f"Booked {slot.start:%Y-%m-%d %H:%M} for {item.group_type.title} {group.number}"}
