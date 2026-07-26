from datetime import timedelta

from django.db.models import Max

from courses.models import Course, Group, GroupType, HandoffItem, HandoffSlot, Student
from iam.models import User


class CourseRepository:
    @staticmethod
    def list_courses():
        return Course.objects.prefetch_related("professors", "head_tas", "tas", "students").all()

    @staticmethod
    async def get_course(course_id: int) -> Course:
        return await Course.objects.prefetch_related("professors", "head_tas", "tas", "students").aget(pk=course_id)

    @staticmethod
    async def create_course(*, code: str, name: str, semester: str = "", description: str = "") -> Course:
        course = await Course.objects.acreate(code=code, name=name, semester=semester, description=description)
        return await CourseRepository.get_course(course.id)

    @staticmethod
    async def update_course(course: Course, **fields) -> Course:
        for field, value in fields.items():
            if value is not None:
                setattr(course, field, value)
        await course.asave()
        return course

    @staticmethod
    async def delete_course(course: Course) -> None:
        await course.adelete()

    @staticmethod
    async def add_professor(course: Course, user: User) -> None:
        await course.professors.aadd(user)

    @staticmethod
    async def remove_professor(course: Course, user: User) -> None:
        await course.professors.aremove(user)

    @staticmethod
    async def add_head_ta(course: Course, user: User) -> None:
        await course.head_tas.aadd(user)

    @staticmethod
    async def remove_head_ta(course: Course, user: User) -> None:
        await course.head_tas.aremove(user)

    @staticmethod
    async def add_ta(course: Course, user: User) -> None:
        await course.tas.aadd(user)

    @staticmethod
    async def remove_ta(course: Course, user: User) -> None:
        await course.tas.aremove(user)

    @staticmethod
    async def has_action(user: User, action_name: str) -> bool:
        return await user.roles.filter(actions__name=action_name).aexists()

    @staticmethod
    async def is_instructor(course: Course, user: User) -> bool:
        """Professors and head TAs of this course - and nobody else.

        Unlike `is_professor_or_head_ta`, superusers get no shortcut: running the
        server is not the same as teaching the course.
        """
        return await course.professors.filter(pk=user.pk).aexists() or await course.head_tas.filter(pk=user.pk).aexists()

    @staticmethod
    async def is_professor_or_head_ta(course: Course, user: User) -> bool:
        if user.is_superuser:
            return True
        return await course.professors.filter(pk=user.pk).aexists() or await course.head_tas.filter(pk=user.pk).aexists()

    @staticmethod
    async def is_ta(course: Course, user: User) -> bool:
        return await course.tas.filter(pk=user.pk).aexists()


class GroupRepository:
    @staticmethod
    def list_types(course_id: int):
        return GroupType.objects.filter(course_id=course_id).prefetch_related("groups__members")

    @staticmethod
    async def get_type(type_pk: int) -> GroupType:
        return await GroupType.objects.select_related("course").prefetch_related("groups__members").aget(pk=type_pk)

    @staticmethod
    async def create_type(*, course: Course, **fields) -> GroupType:
        group_type = await GroupType.objects.acreate(course=course, **fields)
        return await GroupRepository.get_type(group_type.pk)

    @staticmethod
    async def update_type(group_type: GroupType, **fields) -> GroupType:
        for field, value in fields.items():
            if value is not None:
                setattr(group_type, field, value)
        await group_type.asave()
        return await GroupRepository.get_type(group_type.pk)

    @staticmethod
    async def set_signup_token(group_type: GroupType, token) -> None:
        """Its own setter because `update_type` treats None as "leave alone"."""
        group_type.signup_token = token
        await group_type.asave(update_fields=["signup_token", "updated_at"])

    @staticmethod
    async def delete_type(group_type: GroupType) -> None:
        await group_type.adelete()

    @staticmethod
    async def get_group(group_pk: int) -> Group:
        return await Group.objects.select_related("type__course").prefetch_related("members").aget(pk=group_pk)

    @staticmethod
    async def add_group(group_type: GroupType) -> Group:
        """Groups of a type are numbered 1, 2, 3...; the next one takes the next free number."""
        last = await group_type.groups.aaggregate(highest=Max("number"))
        return await Group.objects.acreate(type=group_type, number=(last["highest"] or 0) + 1)

    @staticmethod
    async def delete_group(group: Group) -> None:
        await group.adelete()

    @staticmethod
    async def member_count(group: Group) -> int:
        return await group.members.acount()

    @staticmethod
    async def join(student: Student, group: Group) -> None:
        """Groups of one type are mutually exclusive, so joining leaves the siblings."""
        async for sibling in Group.objects.filter(type_id=group.type_id, members=student).exclude(pk=group.pk):
            await sibling.members.aremove(student)
        await group.members.aadd(student)

    @staticmethod
    async def leave(student: Student, group: Group) -> None:
        await group.members.aremove(student)


class StudentRepository:
    @staticmethod
    def list_students(course_id: int):
        return Student.objects.filter(course_id=course_id)

    @staticmethod
    async def get_student(student_pk: int) -> Student:
        return await Student.objects.select_related("course").aget(pk=student_pk)

    @staticmethod
    async def create_student(*, course: Course, student_id: str, name: str = "") -> Student:
        return await Student.objects.acreate(course=course, student_id=student_id, name=name)

    @staticmethod
    async def update_student(student: Student, **fields) -> Student:
        for field, value in fields.items():
            if value is not None:
                setattr(student, field, value)
        await student.asave()
        return student

    @staticmethod
    async def delete_student(student: Student) -> None:
        await student.adelete()


class HandoffRepository:
    @staticmethod
    def list_items(course_id: int):
        return HandoffItem.objects.filter(course_id=course_id).prefetch_related(
            "slots__ta", "slots__group__members", "slots__booked_by"
        )

    @staticmethod
    async def get_item(item_pk: int) -> HandoffItem:
        return await HandoffItem.objects.select_related("course", "group_type").prefetch_related(
            "slots__ta", "slots__group__members", "slots__booked_by"
        ).aget(pk=item_pk)

    @staticmethod
    async def create_item(*, course: Course, group_type: GroupType, **fields) -> HandoffItem:
        item = await HandoffItem.objects.acreate(course=course, group_type=group_type, **fields)
        return await HandoffRepository.get_item(item.pk)

    @staticmethod
    async def update_item(item: HandoffItem, **fields) -> HandoffItem:
        for field, value in fields.items():
            if value is not None:
                setattr(item, field, value)
        await item.asave()
        return await HandoffRepository.get_item(item.pk)

    @staticmethod
    async def set_signup_token(item: HandoffItem, token) -> None:
        """Its own setter because `update_item` treats None as "leave alone"."""
        item.signup_token = token
        await item.asave(update_fields=["signup_token", "updated_at"])

    @staticmethod
    async def delete_item(item: HandoffItem) -> None:
        await item.adelete()

    @staticmethod
    async def add_slots(*, item: HandoffItem, ta: User, start, end) -> int:
        """Slice an availability window into back-to-back slots, resting in between.

        A slot that would run past the end of the window is not offered, and a
        window submitted twice does not double up: overlaps with what this TA
        already offers are skipped.
        """
        length = timedelta(minutes=item.slot_minutes)
        step = length + timedelta(minutes=item.break_minutes)
        taken = [
            (slot.start, slot.end)
            async for slot in HandoffSlot.objects.filter(item=item, ta=ta, end__gt=start, start__lt=end)
        ]
        made = 0
        cursor = start
        while cursor + length <= end:
            slot_end = cursor + length
            if not any(cursor < other_end and slot_end > other_start for other_start, other_end in taken):
                await HandoffSlot.objects.acreate(item=item, ta=ta, start=cursor, end=slot_end)
                made += 1
            cursor += step
        return made

    @staticmethod
    async def get_slot(slot_pk: int) -> HandoffSlot:
        return await HandoffSlot.objects.select_related("item__course", "ta").aget(pk=slot_pk)

    @staticmethod
    async def clear_booking(slot: HandoffSlot) -> None:
        """Free the window again, keeping it on offer for someone else."""
        slot.group = None
        slot.booked_by = None
        slot.teammates_confirmed = False
        await slot.asave(update_fields=["group", "booked_by", "teammates_confirmed"])

    @staticmethod
    async def delete_slot(slot: HandoffSlot) -> None:
        await slot.adelete()
