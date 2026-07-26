from typing import Optional

from ninja import ModelSchema, Schema

from grading.models import GradingComponent, GradingSheet, GradingTask, Score, SubGrade
from courses.schemas import StudentSchema
from iam.schemas import UserBriefSchema


class GradingComponentSchema(ModelSchema):
    sheet_id: Optional[int] = None

    @staticmethod
    def resolve_sheet_id(obj) -> Optional[int]:
        """Lets the UI link straight to the sheet without a probe request per component.

        Read from the select_related cache rather than `obj.sheet`: touching the
        relation would fire a query, which the async views cannot do.
        """
        sheet = obj._state.fields_cache.get("sheet")
        return sheet.id if sheet else None

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


class SubGradeSchema(ModelSchema):
    class Meta:
        model = SubGrade
        fields = ["id", "sheet", "name", "max_score"]


class SubGradeCreateSchema(Schema):
    name: str
    max_score: float = 100


class SubGradeUpdateSchema(Schema):
    name: Optional[str] = None
    max_score: Optional[float] = None


class ScoreSchema(ModelSchema):
    class Meta:
        model = Score
        fields = ["id", "subgrade", "student", "value", "comment", "updated_at"]


class ScoreSetSchema(Schema):
    """`null` clears a score without deleting the row.

    Fields left out of the request keep their stored value, so a comment can be
    edited without touching the score and the other way round.
    """

    value: Optional[float] = None
    comment: Optional[str] = None


class GradingSheetSchema(ModelSchema):
    class Meta:
        model = GradingSheet
        fields = ["id", "component", "title", "created_at", "updated_at"]


class GradingSheetCreateSchema(Schema):
    title: str


class GradingSheetUpdateSchema(Schema):
    title: Optional[str] = None


class GradingSheetFullSchema(Schema):
    """Everything the sheet grid needs in one round trip."""

    sheet: GradingSheetSchema
    subgrades: list[SubGradeSchema]
    students: list[StudentSchema]
    scores: list[ScoreSchema]
    can_edit: bool


class ScoreEntrySchema(Schema):
    subgrade: int
    student: int
    value: Optional[float] = None
    comment: Optional[str] = None


class ScoreBulkSchema(Schema):
    """One request per paste, instead of one per cell."""

    scores: list[ScoreEntrySchema]
