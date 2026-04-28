from datetime import date, datetime, timedelta

from django.db.models import Q
from django.http import HttpResponseBadRequest, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from LoginApp.decorators import session_login_required

from .models import (
    BookingForSubject,
    BookingForSubjectForm,
    BookingForTutoring,
    BookingForTutoringForm,
    Blackout,
    Room,
)
from .notifications import notify_admins_new_booking, notify_booker_status_change
from .utils import ALL_DAYS_ORDERED, range_to_days_list

BOOKING_MODELS = {
    "subject": BookingForSubject,
    "tutoring": BookingForTutoring,
}


@session_login_required
def Home(request):
    data = {
        "username": request.session.get("display_name")
        or request.session.get("username"),
    }
    return render(request, "Bookingapp/home.html", data)


@session_login_required
def BookingView(request):
    rooms = Room.objects.filter(is_active=True)
    data = {"Roomlist": rooms}
    return render(request, "Bookingapp/booking.html", data)


@session_login_required
def Confirmbooking(request, id):
    room = get_object_or_404(Room, room_id=id)
    username_save = request.session["username"]

    initial = {
        "date_start": request.GET.get("date_start"),
        "date_end": request.GET.get("date_end"),
        "time_start": request.GET.get("time_start"),
        "time_end": request.GET.get("time_end"),
    }
    initial = {k: v for k, v in initial.items() if v}

    subject_form = BookingForSubjectForm(prefix="subject", initial=initial)
    tutoring_form = BookingForTutoringForm(prefix="tutoring", initial=initial)
    success = False
    conflict_error = None

    if request.method == "POST":
        booking_type = request.POST.get("booking_type", "")
        form_cls, prefix = (
            (BookingForSubjectForm, "subject")
            if booking_type == "subject"
            else (BookingForTutoringForm, "tutoring")
        )
        bound = form_cls(request.POST, prefix=prefix)
        if booking_type == "subject":
            subject_form = bound
        else:
            tutoring_form = bound

        if bound.is_valid():
            booking = bound.save(commit=False)
            booking.username = username_save
            booking.display_name = request.session.get("display_name", "")
            booking.email = request.session.get("email", "")
            booking.room = room
            booking.booking_type = booking_type
            booking.status = "pending"

            conflicts = check_booking_conflict(
                room=booking.room,
                date_start=booking.date_start,
                date_end=booking.date_end,
                days_of_week=booking.days_of_week,
                time_start=booking.time_start,
                time_end=booking.time_end,
            )
            blackouts = check_blackout_conflict(
                room=booking.room,
                date_start=booking.date_start,
                date_end=booking.date_end,
            )
            if conflicts:
                conflict_error = (
                    "ห้องนี้ถูกจองในช่วงเวลาที่ซ้ำกันแล้ว กรุณาเลือกวัน/เวลาอื่น"
                )
            elif blackouts:
                conflict_error = (
                    "ช่วงวันที่เลือกอยู่ในช่วงที่ห้องไม่เปิดให้จอง"
                )
            else:
                booking.save()
                notify_admins_new_booking(booking)
                success = True

    data = {
        "subject_form": subject_form,
        "tutoring_form": tutoring_form,
        "room": room,
        "User": request.session.get("username"),
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
    """Return live (pending/approved) bookings whose time range overlaps."""

    conflicts = []
    new_days = set(range_to_days_list(days_of_week))

    for Model in (BookingForSubject, BookingForTutoring):
        existing = Model.objects.filter(
            room=room,
            date_start__lte=date_end,
            date_end__gte=date_start,
            time_start__lt=time_end,
            time_end__gt=time_start,
        ).exclude(status__in=["rejected", "cancelled"])
        for booking in existing:
            existing_days = set(range_to_days_list(booking.days_of_week))
            if existing_days & new_days:
                conflicts.append(booking)

    return conflicts


def check_blackout_conflict(room, date_start, date_end):
    """Return blackouts that intersect the date range for this room (or globally).

    A blackout with room=NULL applies to all rooms; use Q objects to match both
    cases because Django's __in lookup does not match NULL FK values.
    """
    return list(
        Blackout.objects.filter(
            date_start__lte=date_end,
            date_end__gte=date_start,
        ).filter(Q(room=room) | Q(room__isnull=True))
    )


@session_login_required
def Booked(request):
    username = request.session["username"]
    subjects = BookingForSubject.objects.filter(username=username).order_by(
        "-created_at"
    )
    tutorings = BookingForTutoring.objects.filter(username=username).order_by(
        "-created_at"
    )
    today = date.today()
    data = {"subjects": subjects, "tutorings": tutorings, "today": today}
    return render(request, "Bookingapp/booked.html", data)


@session_login_required
@require_POST
def cancel_booking(request, kind, pk):
    Model = BOOKING_MODELS.get(kind)
    if Model is None:
        return HttpResponseBadRequest("unknown booking kind")

    booking = get_object_or_404(Model, pk=pk)

    if booking.username != request.session.get("username"):
        return redirect("booked")

    if booking.status in {"cancelled", "rejected"}:
        return redirect("booked")

    booking.status = "cancelled"
    booking.decided_at = timezone.now()
    booking.decided_by = request.session.get("username", "")
    booking.save()

    notify_booker_status_change(booking)
    return redirect("booked")


@session_login_required
def calendar_view(request):
    rooms = Room.objects.filter(is_active=True)
    return render(
        request,
        "Bookingapp/calendar.html",
        {"rooms": rooms, "selected_room": request.GET.get("room", "")},
    )


@session_login_required
def calendar_events_json(request):
    """FullCalendar JSON feed.

    Expands each booking into per-day events using the days_of_week field.
    Filters by ?room=<room_id>. Excludes rejected/cancelled bookings.
    """

    start = _parse_iso_date(request.GET.get("start"))
    end = _parse_iso_date(request.GET.get("end"))
    if not start or not end:
        return JsonResponse([], safe=False)

    room_filter = request.GET.get("room") or ""

    events = []
    color_for = {"pending": "#f59e0b", "approved": "#10b981"}

    for Model in (BookingForSubject, BookingForTutoring):
        qs = Model.objects.filter(
            date_start__lte=end,
            date_end__gte=start,
        ).exclude(status__in=["rejected", "cancelled"])
        if room_filter:
            qs = qs.filter(room__room_id=room_filter)
        for booking in qs.select_related("room"):
            events.extend(_expand_booking(booking, start, end, color_for))

    blackout_qs = Blackout.objects.filter(
        date_start__lte=end, date_end__gte=start
    )
    if room_filter:
        blackout_qs = blackout_qs.filter(room__in=[None]).union(
            Blackout.objects.filter(
                date_start__lte=end,
                date_end__gte=start,
                room__room_id=room_filter,
            )
        )
    for bo in blackout_qs:
        events.append(
            {
                "title": f"ปิด: {bo.reason or 'ไม่ระบุเหตุผล'}",
                "start": bo.date_start.isoformat(),
                "end": (bo.date_end + timedelta(days=1)).isoformat(),
                "allDay": True,
                "color": "#ef4444",
            }
        )

    return JsonResponse(events, safe=False)


def _parse_iso_date(value):
    if not value:
        return None
    try:
        # FullCalendar sends ISO with timezone, eg "2026-04-01T00:00:00+07:00"
        return datetime.fromisoformat(value.replace("Z", "+00:00")).date()
    except ValueError:
        try:
            return date.fromisoformat(value[:10])
        except ValueError:
            return None


def _expand_booking(booking, window_start, window_end, color_map):
    """Yield FullCalendar events, one per day the booking applies to in window."""

    selected_days = set(range_to_days_list(booking.days_of_week))
    if not selected_days:
        return

    span_start = max(booking.date_start, window_start)
    span_end = min(booking.date_end, window_end)
    title_prefix = (
        getattr(booking, "subject_code", "")
        or getattr(booking, "title", "")
        or "Booking"
    )

    color = color_map.get(booking.status, "#6b7280")
    cur = span_start
    while cur <= span_end:
        thai_day = ALL_DAYS_ORDERED[cur.weekday()]
        if thai_day in selected_days:
            yield {
                "title": f"{title_prefix} ({booking.room.room_name if booking.room else '-'})",
                "start": f"{cur.isoformat()}T{booking.time_start.isoformat()}",
                "end": f"{cur.isoformat()}T{booking.time_end.isoformat()}",
                "color": color,
                "extendedProps": {
                    "status": booking.status,
                    "booker": booking.display_name or booking.username,
                },
            }
        cur += timedelta(days=1)
