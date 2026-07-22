from courses.models import Course
from iam.models import User


class CourseRepository:
    @staticmethod
    def list_courses():
        return Course.objects.prefetch_related("professors", "head_tas", "tas").all()

    @staticmethod
    async def get_course(course_id: int) -> Course:
        return await Course.objects.prefetch_related("professors", "head_tas", "tas").aget(pk=course_id)

    @staticmethod
    async def create_course(*, code: str, name: str, description: str = "") -> Course:
        course = await Course.objects.acreate(code=code, name=name, description=description)
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
    async def is_professor_or_head_ta(course: Course, user: User) -> bool:
        if user.is_superuser:
            return True
        return await course.professors.filter(pk=user.pk).aexists() or await course.head_tas.filter(pk=user.pk).aexists()

    @staticmethod
    async def is_ta(course: Course, user: User) -> bool:
        return await course.tas.filter(pk=user.pk).aexists()
