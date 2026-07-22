from django.contrib import admin

from grading.models import GradingComponent, GradingTask


@admin.register(GradingComponent)
class GradingComponentAdmin(admin.ModelAdmin):
    list_display = ("course", "name", "weight", "created_at")
    search_fields = ("course__code", "name")


@admin.register(GradingTask)
class GradingTaskAdmin(admin.ModelAdmin):
    list_display = ("component", "assigned_to", "assigned_by", "created_at")
    search_fields = ("component__name", "assigned_to__username")
