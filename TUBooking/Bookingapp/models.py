from django.db import models
from django import forms

# Create your models here.
class User(models.Model):
    user_id = models.CharField(max_length=30)
    name = models.CharField(max_length=100)
    email = models.CharField(max_length=50)
    username = models.CharField(max_length=50)
    password = models.CharField(max_length=50)
    #there 2 role : lecturer, admin
    role = models.CharField(max_length=20)

class Room(models.Model):
    room_id = models.CharField(max_length=10)
    room_name = models.CharField(max_length=100)
    room_capacity = models.IntegerField(default=0)
    room_info = models.CharField(max_length=100)

class Booking(models.Model):
    room_id = models.CharField(max_length=10)
    booking_type = models.CharField(max_length=100)
    date_start = models.CharField(max_length=100)
    date_end = models.CharField(max_length=100)
    week_type  = models.CharField(max_length=100)
    time_start = models.CharField(max_length=100)
    time_end = models.CharField(max_length=100)
    username = models.CharField(max_length=50)

class LoginForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('username', 'password')
        labels = {
            'username': 'Username',
            'password': 'Password'
        }

class confirmbookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ('booking_type', 'date_start','date_end','week_type','time_start','time_end')
        labels = {
            'booking_type': 'Booking type',
            'date_start': 'Date start',
            'date_end': 'Date end',
            'week_type': 'Week type',
            'time_start': 'Time start',
            'time_end': 'Time end',
        }

class RegisterForm(forms.Form):
    user_id       = forms.CharField(max_length=30, label='Student/Staff ID')
    name          = forms.CharField(max_length=100, label='Full Name')
    email         = forms.EmailField(max_length=50, label='Email')
    username      = forms.CharField(max_length=50, label='Username')
    password      = forms.CharField(max_length=50, label='Password',
                                    widget=forms.PasswordInput)
    confirm_password = forms.CharField(max_length=50, label='Confirm Password',
                                       widget=forms.PasswordInput)

    def clean(self):
        cleaned = super().clean()
        pw  = cleaned.get('password')
        cpw = cleaned.get('confirm_password')
        if pw and cpw and pw != cpw:
            raise forms.ValidationError('Passwords do not match.')
        return cleaned
