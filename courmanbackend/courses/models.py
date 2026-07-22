from django.conf import settings
from django.db import models


class Course(models.Model):
    code = models.CharField(max_length=32, unique=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    professors = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name="courses_as_professor", blank=True)
    head_tas = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name="courses_as_head_ta", blank=True)
    tas = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name="courses_as_ta", blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["code"]

    def __str__(self):
        return f"{self.code} - {self.name}"
