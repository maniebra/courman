from typing import Optional

from ninja import ModelSchema, Schema

from grading.models import GradingComponent, GradingTask
from iam.schemas import UserBriefSchema


class GradingComponentSchema(ModelSchema):
    class Meta:
        model = GradingComponent
        fields = ["id", "course", "name", "weight", "created_at", "updated_at"]


class GradingComponentCreateSchema(Schema):
    name: str
    weight: float


class GradingComponentUpdateSchema(Schema):
    name: Optional[str] = None
    weight: Optional[float] = None


class GradingTaskSchema(ModelSchema):
    assigned_to: UserBriefSchema
    assigned_by: UserBriefSchema

    class Meta:
        model = GradingTask
        fields = ["id", "component", "created_at"]


class GradingTaskCreateSchema(Schema):
    assigned_to_id: int
