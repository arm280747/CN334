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
]
