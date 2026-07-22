from django.contrib import admin

from profiles.models import Profile


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "phone_number", "created_at", "updated_at")
    search_fields = ("user__username", "phone_number")
