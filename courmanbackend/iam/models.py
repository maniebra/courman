from django.conf import settings
from django.db import models
from django.contrib.auth.models import AbstractUser


def default_language():
    return settings.APP_DEFAULT_LANGUAGE


class AppSettings(models.Model):
    """Single row (pk=1) of settings that apply to everyone, admin-editable."""

    LANGUAGES = [("en", "English"), ("fa", "فارسی")]

    language = models.CharField(max_length=2, choices=LANGUAGES, default=default_language)

    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)


class User(AbstractUser):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    roles = models.ManyToManyField("Role", related_name="users", blank=True)

    def __str__(self):
        return self.username


class Role(models.Model):
    name = models.CharField(max_length=64, unique=True)

    actions = models.ManyToManyField("RoleAction", related_name="roles", blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class RoleAction(models.Model):
    name = models.CharField(max_length=64, unique=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name
