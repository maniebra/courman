from django.conf import settings
from django.db import models

from courses.models import Course


class GradingComponent(models.Model):
    course = models.ForeignKey(Course, related_name="grading_components", on_delete=models.CASCADE)
    name = models.CharField(max_length=128)
    weight = models.DecimalField(max_digits=5, decimal_places=2, help_text="Percentage weight toward the final grade")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["course", "name"]
        unique_together = ["course", "name"]

    def __str__(self):
        return f"{self.course.code} - {self.name}"


class GradingTask(models.Model):
    component = models.ForeignKey(GradingComponent, related_name="tasks", on_delete=models.CASCADE)
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="grading_tasks", on_delete=models.CASCADE)
    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="assigned_grading_tasks", on_delete=models.CASCADE
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        unique_together = ["component", "assigned_to"]

    def __str__(self):
        return f"{self.assigned_to} grades {self.component}"
