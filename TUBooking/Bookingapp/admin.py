from django.contrib import admin
from .models import User, Room, BookingForSubject, BookingForTutoring

# Register your models here.
admin.site.register(User)
admin.site.register(Room)
admin.site.register(BookingForSubject)
admin.site.register(BookingForTutoring)
