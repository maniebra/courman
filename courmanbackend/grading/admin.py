from django.contrib import admin

from grading.models import GradingComponent, GradingSheet, GradingTask, Score, SubGrade


@admin.register(GradingComponent)
class GradingComponentAdmin(admin.ModelAdmin):
    list_display = ("course", "name", "weight", "created_at")
    search_fields = ("course__code", "name")


@admin.register(GradingTask)
class GradingTaskAdmin(admin.ModelAdmin):
    list_display = ("component", "assigned_to", "assigned_by", "created_at")
    search_fields = ("component__name", "assigned_to__username")


@admin.register(GradingSheet)
class GradingSheetAdmin(admin.ModelAdmin):
    list_display = ("title", "component", "created_at")
    search_fields = ("title", "component__name")


@admin.register(SubGrade)
class SubGradeAdmin(admin.ModelAdmin):
    list_display = ("name", "sheet", "max_score")
    search_fields = ("name", "sheet__title")


@admin.register(Score)
class ScoreAdmin(admin.ModelAdmin):
    list_display = ("student", "subgrade", "value", "graded_by", "updated_at")
    search_fields = ("student__username", "subgrade__name")
