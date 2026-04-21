from django.shortcuts import render, redirect
from .models import (
    User,
    LoginForm,
    Room,
    BookingForTutoringForm,
    BookingForSubjectForm,
    BookingForSubject,
    BookingForTutoring,
)
from .utils import range_to_days_list
from django.http import HttpResponse


# Create your views here.
def Home(request):

    username = request.session.get("username")
    if username is None:
        return redirect("login")
    print(username)

    data = {"username": username}

    return render(request, "Bookingapp/home.html", data)


def BookingView(request):

    username = request.session.get("username")
    if username is None:
        return redirect("login")

    room = Room.objects.all()

    data = {"Roomlist": room}

    return render(request, "Bookingapp/booking.html", data)


def Confirmbooking(request, id):

    username = request.session.get("username")
    if username is None:
        return redirect("login")

    room = Room.objects.get(room_id=id)
    username_save = username

    subject_form = BookingForSubjectForm(prefix="subject")
    tutoring_form = BookingForTutoringForm(prefix="tutoring")
    success = False
    conflict_error = None

    if request.method == "POST":
        booking_type = request.POST.get("booking_type", "")

        if booking_type == "subject":
            subject_form = BookingForSubjectForm(request.POST, prefix="subject")
            if subject_form.is_valid():
                booking = subject_form.save(commit=False)
                booking.username = username_save
                booking.room = room
                booking.booking_type = "subject"

                conflicts = check_booking_conflict(
                    room=booking.room,
                    date_start=booking.date_start,
                    date_end=booking.date_end,
                    days_of_week=booking.days_of_week,
                    time_start=booking.time_start,
                    time_end=booking.time_end,
                )
                if conflicts:
                    conflict_error = "ห้องนี้ถูกจองในช่วงเวลาที่ซ้ำกันแล้ว กรุณาเลือกวัน/เวลาอื่น"
                else:
                    booking.save()
                    success = True

        elif booking_type == "tutoring":
            tutoring_form = BookingForTutoringForm(request.POST, prefix="tutoring")
            if tutoring_form.is_valid():
                booking = tutoring_form.save(commit=False)
                booking.username = username_save
                booking.room = room
                booking.booking_type = "tutoring"

                conflicts = check_booking_conflict(
                    room=booking.room,
                    date_start=booking.date_start,
                    date_end=booking.date_end,
                    days_of_week=booking.days_of_week,
                    time_start=booking.time_start,
                    time_end=booking.time_end,
                )
                if conflicts:
                    conflict_error = "ห้องนี้ถูกจองในช่วงเวลาที่ซ้ำกันแล้ว กรุณาเลือกวัน/เวลาอื่น"
                else:
                    booking.save()
                    success = True

    data = {
        "subject_form": subject_form,
        "tutoring_form": tutoring_form,
        "room": room,
        "User": username,
        "success": success,
        "conflict_error": conflict_error,
        "booking_type": (
            request.POST.get("booking_type", "subject")
            if request.method == "POST"
            else "subject"
        ),
    }
    return render(request, "Bookingapp/confirmbooking.html", data)


def check_booking_conflict(
    room, date_start, date_end, days_of_week, time_start, time_end
):

    conflicts = []
    new_days = set(range_to_days_list(days_of_week))

    for Model in [BookingForSubject, BookingForTutoring]:
        existing = Model.objects.filter(
            # __lt, __gt เป็น dunder methods
            room=room,
            date_start__lte=date_end,  # __lte คือ less than or equal ง่ายๆ คือ date_start <= date_end
            date_end__gte=date_start,  # __gte คือ greater than or equal (แค่นี้น่าจะพอแหละ)
            time_start__lt=time_end,
            time_end__gt=time_start,
        )
        for booking in existing:
            existing_days = set(range_to_days_list(booking.days_of_week))
            # check intersection เช่น existing = {Mon, Wed}, new = {Wed, Fri} จะไม่ได้เพราะวันพุธชนกัน
            if existing_days & new_days:
                conflicts.append(booking)

    return conflicts


def Booked(request):

    username = request.session.get("username")
    if username is None:
        return redirect("login")

    subjects = BookingForSubject.objects.all()
    tutorings = BookingForTutoring.objects.all()

    data = {"subjects": subjects, "tutorings": tutorings}

    return render(request, "Bookingapp/booked.html", data)
