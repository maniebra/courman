from django.contrib import admin

from courses.models import Course, Group, GroupType, Student


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "semester", "created_at", "updated_at")
    search_fields = ("code", "name", "semester")
    filter_horizontal = ("professors", "head_tas", "tas")


@admin.register(GroupType)
class GroupTypeAdmin(admin.ModelAdmin):
    list_display = ("title", "course", "min_members", "max_members")
    search_fields = ("title", "course__code")
    list_filter = ("course",)


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ("type", "number")
    list_filter = ("type",)
    filter_horizontal = ("members",)


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ("student_id", "name", "course")
    search_fields = ("student_id", "name", "course__code")
    list_filter = ("course",)
