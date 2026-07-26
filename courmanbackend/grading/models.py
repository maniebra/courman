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


class GradingSheet(models.Model):
    """The score matrix for one grading component: sub-grades down the columns,
    the course's students down the rows."""

    component = models.OneToOneField(GradingComponent, related_name="sheet", on_delete=models.CASCADE)
    title = models.CharField(max_length=128)
    #: set to publish a read-only copy at /sheets/<token>; cleared to unpublish
    public_token = models.UUIDField(null=True, blank=True, unique=True, default=None)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.component} sheet"


class SubGrade(models.Model):
    sheet = models.ForeignKey(GradingSheet, related_name="subgrades", on_delete=models.CASCADE)
    name = models.CharField(max_length=128)
    max_score = models.DecimalField(max_digits=6, decimal_places=2, default=100)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["id"]
        unique_together = ["sheet", "name"]

    def __str__(self):
        return f"{self.sheet} - {self.name}"


class Score(models.Model):
    subgrade = models.ForeignKey(SubGrade, related_name="scores", on_delete=models.CASCADE)
    student = models.ForeignKey("courses.Student", related_name="scores", on_delete=models.CASCADE)
    value = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    comment = models.TextField(blank=True, default="")
    graded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="given_scores", on_delete=models.SET_NULL, null=True
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["subgrade", "student"]
        unique_together = ["subgrade", "student"]

    def __str__(self):
        return f"{self.student} - {self.subgrade}: {self.value}"
