from courses.models import Course
from grading.models import GradingComponent, GradingTask
from iam.models import User


class GradingComponentRepository:
    @staticmethod
    def list_components(course_id: int):
        return GradingComponent.objects.filter(course_id=course_id)

    @staticmethod
    async def get_component(component_id: int) -> GradingComponent:
        return await GradingComponent.objects.select_related("course").aget(pk=component_id)

    @staticmethod
    async def create_component(*, course: Course, name: str, weight) -> GradingComponent:
        return await GradingComponent.objects.acreate(course=course, name=name, weight=weight)

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
