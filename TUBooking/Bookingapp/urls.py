from django.urls import path
from . import views


urlpatterns = [
    path("home/", views.Home, name="home"),
    path("booking/", views.BookingView, name="booking"),
    path(
        "confirmbooking/<path:id>/",
        views.Confirmbooking,
        name="confirmbooking",
    ),
    path("booked/", views.Booked, name="booked"),
    path("booking/cancel/<str:kind>/<int:pk>/", views.cancel_booking, name="cancel_booking"),
    path("calendar/", views.calendar_view, name="calendar"),
    path("calendar/events/", views.calendar_events_json, name="calendar_events"),
]
