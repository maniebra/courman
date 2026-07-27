from django.db.models import Q

from courses.models import Course
from grading.models import GradingComponent, GradingSheet, GradingTask, Score, SubGrade
from iam.models import User


class GradingComponentRepository:
    @staticmethod
    def list_components(course_id: int):
        return GradingComponent.objects.filter(course_id=course_id).prefetch_related("sheets")

    @staticmethod
    async def get_component(component_id: int) -> GradingComponent:
        return await GradingComponent.objects.select_related("course").prefetch_related("sheets").aget(pk=component_id)

    @staticmethod
    async def create_component(*, course: Course, name: str, weight) -> GradingComponent:
        component = await GradingComponent.objects.acreate(course=course, name=name, weight=weight)
        return await GradingComponentRepository.get_component(component.id)

    @staticmethod
    async def set_public_token(component: GradingComponent, token) -> None:
        """Its own setter because `update_component` treats None as "leave alone"."""
        component.public_token = token
        await component.asave(update_fields=["public_token", "updated_at"])

    @staticmethod
    async def update_component(component: GradingComponent, **fields) -> GradingComponent:
        for field, value in fields.items():
            if value is not None:
                setattr(component, field, value)
        await component.asave()
        return component

    @staticmethod
    async def delete_component(component: GradingComponent) -> None:
        await component.adelete()


class GradingTaskRepository:
    @staticmethod
    def list_tasks(component_id: int):
        return GradingTask.objects.filter(component_id=component_id).select_related("assigned_to", "assigned_by")

    @staticmethod
    async def get_task(task_id: int) -> GradingTask:
        return await GradingTask.objects.select_related("component__course", "assigned_to", "assigned_by").aget(
            pk=task_id
        )

    @staticmethod
    async def create_task(
        *, component: GradingComponent, assigned_to: User, assigned_by: User, subgrade: SubGrade | None = None
    ) -> GradingTask:
        task = await GradingTask.objects.acreate(
            component=component, subgrade=subgrade, assigned_to=assigned_to, assigned_by=assigned_by
        )
        return await GradingTaskRepository.get_task(task.id)

    @staticmethod
    async def delete_task(task: GradingTask) -> None:
        await task.adelete()


class GradingSheetRepository:
    @staticmethod
    async def get_sheet(sheet_id: int) -> GradingSheet:
        return await GradingSheet.objects.select_related("component__course").aget(pk=sheet_id)

    @staticmethod
    def list_sheets(component_id: int):
        return GradingSheet.objects.filter(component_id=component_id).select_related("component__course")

    @staticmethod
    async def create_sheet(*, component: GradingComponent, title: str) -> GradingSheet:
        sheet = await GradingSheet.objects.acreate(component=component, title=title)
        return await GradingSheetRepository.get_sheet(sheet.pk)

    @staticmethod
    async def update_sheet(sheet: GradingSheet, **fields) -> GradingSheet:
        for field, value in fields.items():
            if value is not None:
                setattr(sheet, field, value)
        await sheet.asave()
        return sheet

    @staticmethod
    async def set_public_token(sheet: GradingSheet, token) -> None:
        """Its own setter because `update_sheet` treats None as "leave alone"."""
        sheet.public_token = token
        await sheet.asave(update_fields=["public_token", "updated_at"])

    @staticmethod
    async def delete_sheet(sheet: GradingSheet) -> None:
        await sheet.adelete()

    @staticmethod
    def list_subgrades(sheet_id: int):
        return SubGrade.objects.filter(sheet_id=sheet_id)

    @staticmethod
    async def get_subgrade(subgrade_id: int) -> SubGrade:
        return await SubGrade.objects.select_related("sheet__component__course").aget(pk=subgrade_id)

    @staticmethod
    async def create_subgrade(*, sheet: GradingSheet, name: str, max_score) -> SubGrade:
        return await SubGrade.objects.acreate(sheet=sheet, name=name, max_score=max_score)

    @staticmethod
    async def update_subgrade(subgrade: SubGrade, **fields) -> SubGrade:
        for field, value in fields.items():
            if value is not None:
                setattr(subgrade, field, value)
        await subgrade.asave()
        return subgrade

    @staticmethod
    async def delete_subgrade(subgrade: SubGrade) -> None:
        await subgrade.adelete()

    @staticmethod
    def list_scores(sheet_id: int):
        return Score.objects.filter(subgrade__sheet_id=sheet_id)

    @staticmethod
    async def set_score(*, subgrade: SubGrade, student: User, graded_by: User, **fields) -> Score:
        """`fields` carries only what the request actually sent (value, comment)."""
        score, _ = await Score.objects.aupdate_or_create(
            subgrade=subgrade,
            student=student,
            defaults={**fields, "graded_by": graded_by},
        )
        return score

    @staticmethod
    async def has_task(component_id: int, user: User, subgrade_id: int | None = None) -> bool:
        """A whole-component task covers every column; a scoped one only its own."""
        tasks = GradingTask.objects.filter(component_id=component_id, assigned_to=user)
        if subgrade_id is None:
            return await tasks.aexists()
        return await tasks.filter(Q(subgrade__isnull=True) | Q(subgrade_id=subgrade_id)).aexists()

    @staticmethod
    async def graded_subgrade_ids(component_id: int, user: User) -> list[int]:
        """The columns this user may fill, or [] when they may fill all of them."""
        return [
            task.subgrade_id
            async for task in GradingTask.objects.filter(component_id=component_id, assigned_to=user)
            if task.subgrade_id is not None
        ]
