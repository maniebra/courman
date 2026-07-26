from courses.models import Course
from grading.models import GradingComponent, GradingSheet, GradingTask, Score, SubGrade
from iam.models import User


class GradingComponentRepository:
    @staticmethod
    def list_components(course_id: int):
        return GradingComponent.objects.filter(course_id=course_id).select_related("sheet")

    @staticmethod
    async def get_component(component_id: int) -> GradingComponent:
        return await GradingComponent.objects.select_related("course", "sheet").aget(pk=component_id)

    @staticmethod
    async def create_component(*, course: Course, name: str, weight) -> GradingComponent:
        component = await GradingComponent.objects.acreate(course=course, name=name, weight=weight)
        return await GradingComponentRepository.get_component(component.id)

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
    async def create_task(*, component: GradingComponent, assigned_to: User, assigned_by: User) -> GradingTask:
        task = await GradingTask.objects.acreate(component=component, assigned_to=assigned_to, assigned_by=assigned_by)
        return await GradingTaskRepository.get_task(task.id)

    @staticmethod
    async def delete_task(task: GradingTask) -> None:
        await task.adelete()


class GradingSheetRepository:
    @staticmethod
    async def get_sheet(sheet_id: int) -> GradingSheet:
        return await GradingSheet.objects.select_related("component__course").aget(pk=sheet_id)

    @staticmethod
    async def get_sheet_for_component(component_id: int) -> GradingSheet:
        return await GradingSheet.objects.select_related("component__course").aget(component_id=component_id)

    @staticmethod
    async def create_sheet(*, component: GradingComponent, title: str) -> GradingSheet:
        await GradingSheet.objects.acreate(component=component, title=title)
        return await GradingSheetRepository.get_sheet_for_component(component.id)

    @staticmethod
    async def update_sheet(sheet: GradingSheet, **fields) -> GradingSheet:
        for field, value in fields.items():
            if value is not None:
                setattr(sheet, field, value)
        await sheet.asave()
        return sheet

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
    async def has_task(component_id: int, user: User) -> bool:
        return await GradingTask.objects.filter(component_id=component_id, assigned_to=user).aexists()
