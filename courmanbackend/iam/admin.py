from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from iam.models import Role, RoleAction, User


@admin.register(User)
class IamUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (("Roles", {"fields": ("roles",)}),)
    filter_horizontal = UserAdmin.filter_horizontal + ("roles",)


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ("name", "created_at", "updated_at")
    search_fields = ("name",)
    filter_horizontal = ("actions",)


@admin.register(RoleAction)
class RoleActionAdmin(admin.ModelAdmin):
    list_display = ("name", "created_at", "updated_at")
    search_fields = ("name",)
