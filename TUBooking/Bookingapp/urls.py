from django.urls import path
from . import views


urlpatterns = [
    path('', views.Login, name="login"),
    path('login', views.Login, name="login"),
    path('logout', views.Logout, name="logout"),
    path('home', views.Home, name="home"),
    path('booking', views.room_booking, name="booking"),
    path('booked', views.Booked, name="booked"),
    path('confirmbooking/<str:id>', views.Confirmbooking, name="confirmbooking"),
]
