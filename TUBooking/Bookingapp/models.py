from django.db import models
from django import forms
from .utils import days_list_to_range, range_to_days_list


# Create your models here.
class User(models.Model):
    user_id = models.CharField(max_length=30)
    name = models.CharField(max_length=100)
    email = models.CharField(max_length=50)
    username = models.CharField(max_length=50)
    # Password is NOT stored — authentication is delegated to the TU REST API.
    # role: 'lecturer' | 'admin'
    role = models.CharField(max_length=20)


class Room(models.Model):
    room_id = models.CharField(max_length=10)
    room_name = models.CharField(max_length=100)
    room_capacity = models.IntegerField(default=0)
    room_info = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)


class Blackout(models.Model):
    """Date range during which a room (or all rooms) cannot be booked."""

    room = models.ForeignKey(
        Room,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="blackouts",
    )
    date_start = models.DateField()
    date_end = models.DateField()
    reason = models.CharField(max_length=200, blank=True, default="")


# Constant data
BOOKING_TYPE_CHOICES = [
    ("subject", "สอนปกติ/ชดเชย/เสริม"),
    ("tutoring", "จัดอบรม/จัดติว"),
]

STATUS_CHOICES = [
    ("pending", "รออนุมัติ"),
    ("approved", "อนุมัติแล้ว"),
    ("rejected", "ปฏิเสธ"),
    ("cancelled", "ยกเลิก"),
]

CURRICULUM_CHOICES = [
    ("ปริญญาตรีภาคปกติ", "ปริญญาตรีภาคปกติ"),
    ("ปริญญาโท", "ปริญญาโท"),
    ("TEP-TEPE", "TEP-TEPE"),
    ("TU-PINE", "TU-PINE"),
]

ALL_DAYS_ORDERED = ["จันทร์", "อังคาร", "พุธ", "พฤหัสบดี", "ศุกร์", "เสาร์", "อาทิตย์"]

DAY_CHOICES = [(d, d) for d in ALL_DAYS_ORDERED]


class Booking(models.Model):
    booking_type = models.CharField(
        max_length=100,
        choices=BOOKING_TYPE_CHOICES,
    )
    date_start = models.DateField()
    date_end = models.DateField()
    # Stores selected days in range notation
    days_of_week = models.CharField(max_length=200, default="")
    time_start = models.TimeField()
    time_end = models.TimeField()
    username = models.CharField(max_length=50)
    display_name = models.CharField(max_length=200, blank=True, default="")
    email = models.CharField(max_length=200, blank=True, default="")

    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="pending"
    )
    denial_reason = models.CharField(max_length=300, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    decided_at = models.DateTimeField(null=True, blank=True)
    decided_by = models.CharField(max_length=50, blank=True, default="")

    class Meta:
        abstract = True


class BookingForSubject(Booking):
    room = models.ForeignKey(
        Room,
        on_delete=models.CASCADE,
        related_name="subject_room",
        null=True,
        blank=True,
    )
    subject_code = models.CharField(max_length=10)
    subject_name = models.CharField(max_length=100)
    curriculum = models.CharField(max_length=100, choices=CURRICULUM_CHOICES)


class BookingForTutoring(Booking):
    room = models.ForeignKey(
        Room,
        on_delete=models.CASCADE,
        related_name="tutoring_room",
        null=True,
        blank=True,
    )
    title = models.CharField(max_length=100)
    detail = models.CharField(max_length=500)


class LoginForm(forms.Form):
    """Plain form — username and password are forwarded to the TU REST API,
    never persisted in the database."""

    username = forms.CharField(
        label="Username",
        widget=forms.TextInput(attrs={"class": "form-control", "id": "username"}),
    )
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={"class": "form-control", "id": "password"}),
    )


# Form for store booking data
class BookingForSubjectForm(forms.ModelForm):
    days_of_week = forms.MultipleChoiceField(
        choices=DAY_CHOICES,
        widget=forms.CheckboxSelectMultiple(attrs={"class": "form-check-input"}),
        label="วันในสัปดาห์",
    )

    class Meta:
        model = BookingForSubject
        fields = [
            "date_start",
            "date_end",
            "days_of_week",
            "time_start",
            "time_end",
            "subject_code",
            "subject_name",
            "curriculum",
        ]

        labels = {
            "date_start": "วันที่เริ่มต้น",
            "date_end": "วันที่สิ้นสุด",
            "time_start": "เวลาเริ่มต้น",
            "time_end": "เวลาสิ้นสุด",
            "subject_code": "รหัสวิชา",
            "subject_name": "ชื่อวิชา",
            "curriculum": "หลักสูตร",
        }

        # DateInput type="date" จะเป็น ปฏิทินเลือกวัน
        # TimeInput type="time" จะเป็น form เลือกเวลา
        # TextInput จะเป็น ช่องกรอกข้อความ
        # Select จะเป็น dropdown
        # class "form-control" / "form-select" เป็นของ bootstrap
        widgets = {
            "date_start": forms.DateInput(
                attrs={"type": "date", "class": "form-control"}
            ),
            "date_end": forms.DateInput(
                attrs={"type": "date", "class": "form-control"}
            ),
            "time_start": forms.TimeInput(
                attrs={"type": "time", "class": "form-control"}
            ),
            "time_end": forms.TimeInput(
                attrs={"type": "time", "class": "form-control"}
            ),
            "subject_code": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "เช่น CN334"}
            ),
            "subject_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "เช่น Software Engineering",
                }
            ),
            "curriculum": forms.Select(attrs={"class": "form-select"}),
        }

    def clean_days_of_week(self):
        """Convert list of selected days to range notation for storage."""
        days = self.cleaned_data.get("days_of_week", [])
        return days_list_to_range(days)


class BookingForTutoringForm(forms.ModelForm):
    days_of_week = forms.MultipleChoiceField(
        choices=DAY_CHOICES,
        widget=forms.CheckboxSelectMultiple(attrs={"class": "form-check-input"}),
        label="วันในสัปดาห์",
    )

    class Meta:
        model = BookingForTutoring
        fields = [
            "date_start",
            "date_end",
            "days_of_week",
            "time_start",
            "time_end",
            "title",
            "detail",
        ]

        labels = {
            "date_start": "วันที่เริ่มต้น",
            "date_end": "วันที่สิ้นสุด",
            "time_start": "เวลาเริ่มต้น",
            "time_end": "เวลาสิ้นสุด",
            "title": "ชื่อเรื่อง",
            "detail": "รายละเอียด",
        }

        widgets = {
            "date_start": forms.DateInput(
                attrs={"type": "date", "class": "form-control"}
            ),
            "date_end": forms.DateInput(
                attrs={"type": "date", "class": "form-control"}
            ),
            "time_start": forms.TimeInput(
                attrs={"type": "time", "class": "form-control"}
            ),
            "time_end": forms.TimeInput(
                attrs={"type": "time", "class": "form-control"}
            ),
            "title": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "ชื่อหัวข้อการอบรม/ติว"}
            ),
            "detail": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "รายละเอียดเพิ่มเติม",
                }
            ),
        }

    def clean_days_of_week(self):
        """Convert list of selected days to range notation for storage."""
        days = self.cleaned_data.get("days_of_week", [])
        return days_list_to_range(days)


class RoomForm(forms.ModelForm):
    class Meta:
        model = Room
        fields = ["room_id", "room_name", "room_capacity", "room_info", "is_active"]
        labels = {
            "room_id": "รหัสห้อง",
            "room_name": "ชื่อห้อง",
            "room_capacity": "ความจุ",
            "room_info": "รายละเอียด",
            "is_active": "เปิดใช้งาน",
        }
        widgets = {
            "room_id": forms.TextInput(attrs={"class": "form-control"}),
            "room_name": forms.TextInput(attrs={"class": "form-control"}),
            "room_capacity": forms.NumberInput(attrs={"class": "form-control"}),
            "room_info": forms.TextInput(attrs={"class": "form-control"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


class BlackoutForm(forms.ModelForm):
    class Meta:
        model = Blackout
        fields = ["room", "date_start", "date_end", "reason"]
        labels = {
            "room": "ห้อง (เว้นว่าง = ทุกห้อง)",
            "date_start": "วันที่เริ่มต้น",
            "date_end": "วันที่สิ้นสุด",
            "reason": "เหตุผล",
        }
        widgets = {
            "room": forms.Select(attrs={"class": "form-select"}),
            "date_start": forms.DateInput(
                attrs={"type": "date", "class": "form-control"}
            ),
            "date_end": forms.DateInput(
                attrs={"type": "date", "class": "form-control"}
            ),
            "reason": forms.TextInput(attrs={"class": "form-control"}),
        }


class RejectForm(forms.Form):
    denial_reason = forms.CharField(
        label="เหตุผลการปฏิเสธ",
        max_length=300,
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 3}),
    )
