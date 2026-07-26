from typing import Optional

from ninja import ModelSchema, Schema

from courses.models import Course, Group, GroupType, Student
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


class GroupSchema(ModelSchema):
    members: list[StudentSchema] = []

    class Meta:
        model = Group
        fields = ["id", "type", "number"]


class GroupTypeSchema(ModelSchema):
    groups: list[GroupSchema] = []

    class Meta:
        model = GroupType
        fields = ["id", "course", "title", "description", "min_members", "max_members", "signup_token"]


class GroupTypeCreateSchema(Schema):
    title: str
    description: str = ""
    min_members: int = 1
    max_members: int = 1


class GroupTypeUpdateSchema(Schema):
    title: Optional[str] = None
    description: Optional[str] = None
    min_members: Optional[int] = None
    max_members: Optional[int] = None
    #: True mints a sign-up token (keeping any existing one), False closes the form
    signup_open: Optional[bool] = None


class GroupSignupFormSchema(Schema):
    """What an anonymous visitor may see: the rules, never the roster."""

    course: str
    title: str
    description: str
    min_members: int
    max_members: int


class GroupSignupSchema(Schema):
    student_ids: list[str]


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
