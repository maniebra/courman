from typing import Optional

from ninja import ModelSchema, Schema

from courses.models import Course, Student
from iam.schemas import UserBriefSchema


class StudentSchema(ModelSchema):
    class Meta:
        model = Student
        fields = ["id", "course", "student_id", "name"]


class StudentCreateSchema(Schema):
    student_id: str
    name: str = ""


class StudentUpdateSchema(Schema):
    student_id: Optional[str] = None
    name: Optional[str] = None


class CourseSchema(ModelSchema):
    professors: list[UserBriefSchema] = []
    head_tas: list[UserBriefSchema] = []
    tas: list[UserBriefSchema] = []
    students: list[StudentSchema] = []

    class Meta:
        model = Course
        fields = ["id", "code", "name", "semester", "description", "created_at", "updated_at"]


class CourseCreateSchema(Schema):
    code: str
    name: str
    semester: str = ""
    description: str = ""


class CourseUpdateSchema(Schema):
    code: Optional[str] = None
    name: Optional[str] = None
    semester: Optional[str] = None
    description: Optional[str] = None
