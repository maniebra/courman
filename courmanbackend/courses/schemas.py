from datetime import datetime
from typing import Optional

from ninja import ModelSchema, Schema

from courses.models import Course, Group, GroupType, HandoffItem, HandoffSlot, Student
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


class HandoffSlotSchema(ModelSchema):
    ta: UserBriefSchema
    group: Optional[GroupSchema] = None
    booked_by: Optional[StudentSchema] = None

    class Meta:
        model = HandoffSlot
        fields = ["id", "start", "end", "teammates_confirmed"]


class HandoffItemSchema(ModelSchema):
    slots: list[HandoffSlotSchema] = []

    class Meta:
        model = HandoffItem
        fields = ["id", "course", "group_type", "title", "description", "signup_token", "hide_ta", "slot_minutes", "break_minutes"]


class HandoffItemCreateSchema(Schema):
    group_type: int
    title: str
    description: str = ""
    hide_ta: bool = True
    slot_minutes: int = 20
    break_minutes: int = 0


class HandoffItemUpdateSchema(Schema):
    title: Optional[str] = None
    description: Optional[str] = None
    signup_open: Optional[bool] = None
    hide_ta: Optional[bool] = None
    slot_minutes: Optional[int] = None
    break_minutes: Optional[int] = None


class HandoffSlotCreateSchema(Schema):
    """A window a TA is available for; the API slices it into slots."""

    start: datetime
    end: datetime
    #: whoever runs the course may offer a window on a TA's behalf; a TA gets themselves
    ta: Optional[int] = None


class PublicSlotSchema(Schema):
    """What a visitor sees: when, with whom, and whether it is still free."""

    id: int
    start: datetime
    end: datetime
    #: empty while the item hides its TAs
    ta: str
    taken: bool


class HandoffFormSchema(Schema):
    course: str
    title: str
    description: str
    group_type: str
    slots: list[PublicSlotSchema]


class HandoffBookingSchema(Schema):
    student_id: str
    slot_id: int
    teammates_confirmed: bool = False
