from django.contrib import admin

from courses.models import Course, Student


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "semester", "created_at", "updated_at")
    search_fields = ("code", "name", "semester")
    filter_horizontal = ("professors", "head_tas", "tas")


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ("student_id", "name", "course")
    search_fields = ("student_id", "name", "course__code")
    list_filter = ("course",)
