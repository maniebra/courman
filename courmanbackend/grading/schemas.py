from typing import Optional

from ninja import ModelSchema, Schema

from grading.models import GradingComponent, GradingSheet, GradingTask, Score, SubGrade
from courses.schemas import StudentSchema
from iam.schemas import UserBriefSchema


class SheetBriefSchema(Schema):
    id: int
    title: str


class GradingComponentSchema(ModelSchema):
    sheets: list[SheetBriefSchema] = []

    @staticmethod
    def resolve_sheets(obj) -> list:
        """Read from the prefetch cache: touching the relation would fire a query,
        which the async views cannot do."""
        return [{"id": sheet.id, "title": sheet.title} for sheet in obj.sheets.all()]

    class Meta:
        model = GradingComponent
        fields = ["id", "course", "name", "weight", "public_token", "created_at", "updated_at"]


class GradingComponentCreateSchema(Schema):
    name: str
    weight: float


class GradingComponentUpdateSchema(Schema):
    name: Optional[str] = None
    weight: Optional[float] = None
    #: True publishes the combined grid (keeping any existing link), False unpublishes
    public: Optional[bool] = None


class GradingTaskSchema(ModelSchema):
    assigned_to: UserBriefSchema
    assigned_by: UserBriefSchema

    class Meta:
        model = GradingTask
        fields = ["id", "component", "subgrade", "created_at"]


class GradingTaskCreateSchema(Schema):
    assigned_to_id: int
    #: leave empty for the whole component, or name one sub-grade to scope the task
    subgrade_id: Optional[int] = None


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
        fields = ["id", "component", "title", "public_token", "created_at", "updated_at"]


class GradingSheetCreateSchema(Schema):
    title: str


class GradingSheetUpdateSchema(Schema):
    title: Optional[str] = None
    #: True publishes the read-only sheet (keeping any existing link), False unpublishes
    public: Optional[bool] = None


class GradingSheetFullSchema(Schema):
    """Everything the sheet grid needs in one round trip."""

    sheet: GradingSheetSchema
    subgrades: list[SubGradeSchema]
    students: list[StudentSchema]
    scores: list[ScoreSchema]
    can_edit: bool
    editable_subgrades: list[int] = []


class PublicCellSchema(Schema):
    value: Optional[float] = None
    comment: str = ""


class PublicScoreRowSchema(Schema):
    student_id: str
    #: one cell per sub-grade, in the same order; empty where nothing is entered
    cells: list[PublicCellSchema]
    total: Optional[float] = None


class PublicSheetSchema(Schema):
    """The published sheet: student IDs, scores and the graders' comments, no names."""

    course: str
    component: str
    title: str
    subgrades: list[str]
    max_scores: list[float]
    rows: list[PublicScoreRowSchema]


class SummaryRowSchema(Schema):
    student_id: str
    name: str = ""
    #: one entry per component, in the same order; None where the sheet has nothing
    totals: list[Optional[float]]
    #: the weighted grade, out of the weights of the components that have a score
    grade: Optional[float] = None


class SummaryComponentSchema(Schema):
    id: int
    name: str
    weight: float
    max_score: float


class GradeSummarySchema(Schema):
    """Every component of a course side by side, one row per student."""

    course: str
    components: list[SummaryComponentSchema]
    rows: list[SummaryRowSchema]
    summary_token: Optional[str] = None


class ComponentSubGradeSchema(Schema):
    id: int
    name: str
    max_score: float


class ComponentSheetSchema(Schema):
    id: int
    title: str
    subgrades: list[ComponentSubGradeSchema]


class ComponentRowSchema(Schema):
    student_id: str
    name: str = ""
    #: one cell per sub-grade of every sheet, in the order the sheets are listed
    cells: list[PublicCellSchema]
    #: the sum of each sheet, in the same order as `sheets`
    sheet_totals: list[Optional[float]]
    total: Optional[float] = None


class ComponentGridSchema(Schema):
    """Every sheet of a component, its columns and the scores behind them."""

    title: str
    sheets: list[ComponentSheetSchema]
    rows: list[ComponentRowSchema]
    public_token: Optional[str] = None


class SummaryPublishSchema(Schema):
    public: bool


class ScoreEntrySchema(Schema):
    subgrade: int
    student: int
    value: Optional[float] = None
    comment: Optional[str] = None


class ScoreBulkSchema(Schema):
    """One request per paste, instead of one per cell."""

    scores: list[ScoreEntrySchema]
