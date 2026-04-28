from django.contrib import admin

from .models import Blackout, BookingForSubject, BookingForTutoring, Room, User


# ── User admin ────────────────────────────────────────────────────────────────

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ["username", "name", "email", "role"]
    list_editable = ["role"]           # change role right from the list
    list_filter = ["role"]
    search_fields = ["username", "name", "email"]
    fields = ["user_id", "username", "name", "email", "role"]


# ── Other models ──────────────────────────────────────────────────────────────

@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ["room_id", "room_name", "room_capacity", "room_info", "is_active"]
    list_editable = ["is_active"]
    list_filter = ["is_active"]


@admin.register(BookingForSubject)
class BookingForSubjectAdmin(admin.ModelAdmin):
    list_display = ["username", "room", "subject_code", "subject_name", "date_start", "date_end", "status"]
    list_filter = ["status"]
    search_fields = ["username", "subject_code"]


@admin.register(BookingForTutoring)
class BookingForTutoringAdmin(admin.ModelAdmin):
    list_display = ["username", "room", "title", "date_start", "date_end", "status"]
    list_filter = ["status"]
    search_fields = ["username", "title"]


@admin.register(Blackout)
class BlackoutAdmin(admin.ModelAdmin):
    list_display = ["room", "date_start", "date_end", "reason"]
