from django.conf import settings
from django.db import models

from courses.models import Course


class GradingComponent(models.Model):
    course = models.ForeignKey(Course, related_name="grading_components", on_delete=models.CASCADE)
    name = models.CharField(max_length=128)
    weight = models.DecimalField(max_digits=5, decimal_places=2, help_text="Percentage weight toward the final grade")
    #: set to publish the read-only combined grid at /components/<token>; cleared to unpublish
    public_token = models.UUIDField(null=True, blank=True, unique=True, default=None)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["course", "name"]
        unique_together = ["course", "name"]

    def __str__(self):
        return f"{self.course.code} - {self.name}"


class GradingTask(models.Model):
    """Who grades what. Left without a sub-grade it covers the whole component;
    pointed at one, the TA may only fill that column - q1 and q2 of the same
    homework can belong to different people."""

    component = models.ForeignKey(GradingComponent, related_name="tasks", on_delete=models.CASCADE)
    subgrade = models.ForeignKey(
        "grading.SubGrade", related_name="tasks", on_delete=models.CASCADE, null=True, blank=True
    )
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="grading_tasks", on_delete=models.CASCADE)
    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="assigned_grading_tasks", on_delete=models.CASCADE
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["component", "assigned_to"],
                condition=models.Q(subgrade__isnull=True),
                name="one_component_task_per_grader",
            ),
            models.UniqueConstraint(
                fields=["subgrade", "assigned_to"],
                condition=models.Q(subgrade__isnull=False),
                name="one_subgrade_task_per_grader",
            ),
        ]

    def __str__(self):
        return f"{self.assigned_to} grades {self.subgrade or self.component}"


class GradingSheet(models.Model):
    """One score matrix: sub-grades down the columns, students down the rows.

    A component may hold several - q1, q2, q3 of one homework - and its total
    is their sums added together.
    """

    component = models.ForeignKey(GradingComponent, related_name="sheets", on_delete=models.CASCADE)
    title = models.CharField(max_length=128)
    #: set to publish a read-only copy at /sheets/<token>; cleared to unpublish
    public_token = models.UUIDField(null=True, blank=True, unique=True, default=None)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["id"]
        unique_together = ["component", "title"]

    def __str__(self):
        return f"{self.component} - {self.title}"


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
