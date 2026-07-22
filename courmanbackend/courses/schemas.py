from typing import Optional

from ninja import ModelSchema, Schema

from courses.models import Course
from iam.schemas import UserBriefSchema


class CourseSchema(ModelSchema):
    professors: list[UserBriefSchema] = []
    head_tas: list[UserBriefSchema] = []
    tas: list[UserBriefSchema] = []

    class Meta:
        model = Course
        fields = ["id", "code", "name", "description", "created_at", "updated_at"]


class CourseCreateSchema(Schema):
    code: str
    name: str
    description: str = ""


class CourseUpdateSchema(Schema):
    code: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
