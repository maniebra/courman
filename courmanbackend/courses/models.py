from django.conf import settings
from django.db import models


class Course(models.Model):
    code = models.CharField(max_length=32)
    name = models.CharField(max_length=255)
    semester = models.CharField(max_length=32, blank=True, default="", help_text="e.g. Fall 2026")
    description = models.TextField(blank=True)

    professors = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name="courses_as_professor", blank=True)
    head_tas = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name="courses_as_head_ta", blank=True)
    tas = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name="courses_as_ta", blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        # the same course runs again every semester, so the code alone is not the key
        ordering = ["-semester", "code"]
        unique_together = ["code", "semester"]

    def __str__(self):
        return f"{self.code} - {self.name}" + (f" ({self.semester})" if self.semester else "")


class GroupType(models.Model):
    """One way of splitting a course into teams, e.g. "Project" or "Lab".

    The size limits live here because they are the same for every group of the
    type. A student joins at most one group per type, but may be in a group of
    each type at once.
    """

    course = models.ForeignKey(Course, related_name="group_types", on_delete=models.CASCADE)
    title = models.CharField(max_length=128)
    description = models.TextField(blank=True, default="")
    min_members = models.PositiveSmallIntegerField(default=1)
    max_members = models.PositiveSmallIntegerField(default=1)
    #: set to open the public sign-up form at /groups/<token>; cleared to close it
    signup_token = models.UUIDField(null=True, blank=True, unique=True, default=None)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["title"]
        unique_together = ["course", "title"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(min_members__lte=models.F("max_members")), name="group_type_min_lte_max"
            ),
        ]

    def __str__(self):
        return f"{self.course.code} - {self.title}"


class Group(models.Model):
    """One numbered team of a type: "Project 1", "Project 2", ..."""

    type = models.ForeignKey(GroupType, related_name="groups", on_delete=models.CASCADE)
    number = models.PositiveSmallIntegerField()
    members = models.ManyToManyField("courses.Student", related_name="groups", blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["number"]
        unique_together = ["type", "number"]

    def __str__(self):
        return f"{self.type.title} {self.number}"


class Student(models.Model):
    """Someone enrolled in a course, identified by their university student ID.

    Deliberately not a `User`: students are rostered by the people running the
    course and never need to sign in, so an account would be dead weight.
    """

    course = models.ForeignKey(Course, related_name="students", on_delete=models.CASCADE)
    student_id = models.CharField(max_length=32)
    name = models.CharField(max_length=255, blank=True, default="")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["student_id"]
        unique_together = ["course", "student_id"]

    def __str__(self):
        return f"{self.student_id} - {self.name}" if self.name else self.student_id
