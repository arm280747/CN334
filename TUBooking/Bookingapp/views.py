from django.shortcuts import render, redirect
from Bookingapp.models import User, LoginForm, Room, confirmbookingForm, Booking
from django.http import HttpResponse


# Create your views here.
def Login(request):
    form = LoginForm()
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            print("there are user table")
            username=form.cleaned_data['username']
            password=form.cleaned_data['password']

            request.session['username'] = username
            request.session['role'] = "lecturer"

            return redirect('home')
          
    data = {
        "form": form,
    }
    return render(request, "Bookingapp/login.html", data)

def Logout(request):

    request.session.flush()

    return redirect('login')


def Home(request):

    username = request.session.get('username')
    if username is None:
       return redirect('login')
    print(username)
    
    data = {
        "username": username
    }

    return render(request, "Bookingapp/home.html", data)

def room_booking(request):

    username = request.session.get('username')

    room = Room.objects.all()
    
    data = {
        "Roomlist": room
    }

    return render(request, "Bookingapp/booking.html", data)

def Confirmbooking(request, id):

    username = request.session.get('username')

    room = Room.objects.get(room_id=id)
    room_id = id
    username_save = username
    
    form = confirmbookingForm()
    if request.method == "POST":
        form = confirmbookingForm(request.POST)
        if form.is_valid():
            booking =form.save(commit=False)
            booking.username = username_save
            booking.room_id = id
            booking.save()

    data = {
        "form": form,
        "roomid": room_id,
        "room": room,
        "User": username
    }
    return render(request, "Bookingapp/confirmbooking.html", data)

def Booked(request):

    username = request.session.get('username')

    Book = Booking.objects.all()
    
    data = {
        "Booked": Book
    }

    return render(request, "Bookingapp/booking.html", data)