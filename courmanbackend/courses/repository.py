from courses.models import Course, Student
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
