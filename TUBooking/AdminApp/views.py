"""Admin panel views — approval, room/user/blackout management, reporting.

All views require an authenticated session whose role == "admin"
(enforced by the ``admin_required`` decorator).
"""

import csv
from datetime import date, datetime, timedelta

from django.http import Http404, HttpResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from Bookingapp.models import (
    Blackout,
    BlackoutForm,
    BookingForSubject,
    BookingForTutoring,
    RejectForm,
    Room,
    RoomForm,
    User,
)
from Bookingapp.notifications import notify_booker_status_change
from LoginApp.decorators import admin_required

BOOKING_MODELS = {
    "subject": BookingForSubject,
    "tutoring": BookingForTutoring,
}


@admin_required
def dashboard(request):
    today = date.today()
    month_start = today.replace(day=1)

    pending_subj = BookingForSubject.objects.filter(status="pending").count()
    pending_tut = BookingForTutoring.objects.filter(status="pending").count()
    approved_this_month = (
        BookingForSubject.objects.filter(
            status="approved", decided_at__gte=month_start
        ).count()
        + BookingForTutoring.objects.filter(
            status="approved", decided_at__gte=month_start
        ).count()
    )

    return render(
        request,
        "AdminApp/dashboard.html",
        {
            "pending_count": pending_subj + pending_tut,
            "approved_this_month": approved_this_month,
            "rooms_total": Room.objects.count(),
            "rooms_active": Room.objects.filter(is_active=True).count(),
            "blackouts": Blackout.objects.count(),
        },
    )


@admin_required
def pending_list(request):
    subjects = BookingForSubject.objects.filter(status="pending").order_by("created_at")
    tutorings = BookingForTutoring.objects.filter(status="pending").order_by(
        "created_at"
    )
    reject_form = RejectForm()
    return render(
        request,
        "AdminApp/pending.html",
        {
            "subjects": subjects,
            "tutorings": tutorings,
            "reject_form": reject_form,
        },
    )


@admin_required
def approve(request, kind, pk):
    if request.method != "POST":
        return HttpResponseBadRequest("POST only")
    booking = _get_booking_or_404(kind, pk)
    booking.status = "approved"
    booking.decided_at = timezone.now()
    booking.decided_by = request.session.get("username", "")
    booking.denial_reason = ""
    booking.save()
    notify_booker_status_change(booking)
    return redirect("admin_pending")


@admin_required
def reject(request, kind, pk):
    if request.method != "POST":
        return HttpResponseBadRequest("POST only")
    booking = _get_booking_or_404(kind, pk)
    form = RejectForm(request.POST)
    if not form.is_valid():
        return redirect("admin_pending")
    booking.status = "rejected"
    booking.denial_reason = form.cleaned_data["denial_reason"]
    booking.decided_at = timezone.now()
    booking.decided_by = request.session.get("username", "")
    booking.save()
    notify_booker_status_change(booking)
    return redirect("admin_pending")


def _get_booking_or_404(kind, pk):
    Model = BOOKING_MODELS.get(kind)
    if Model is None:
        raise Http404
    return get_object_or_404(Model, pk=pk)


# ── Rooms CRUD ───────────────────────────────────────────────────────────────


@admin_required
def room_list(request):
    rooms = Room.objects.all().order_by("room_id")
    return render(request, "AdminApp/rooms.html", {"rooms": rooms})


@admin_required
def room_form(request, pk=None):
    room = get_object_or_404(Room, pk=pk) if pk else None
    if request.method == "POST":
        form = RoomForm(request.POST, instance=room)
        if form.is_valid():
            form.save()
            return redirect("admin_rooms")
    else:
        form = RoomForm(instance=room)
    return render(
        request, "AdminApp/room_form.html", {"form": form, "is_edit": room is not None}
    )


@admin_required
def room_disable(request, pk):
    if request.method != "POST":
        return HttpResponseBadRequest("POST only")
    room = get_object_or_404(Room, pk=pk)
    room.is_active = not room.is_active
    room.save()
    return redirect("admin_rooms")


# ── Users / role management ──────────────────────────────────────────────────


@admin_required
def user_list(request):
    users = User.objects.all().order_by("username")
    return render(request, "AdminApp/users.html", {"users": users})


@admin_required
def user_set_role(request, pk):
    if request.method != "POST":
        return HttpResponseBadRequest("POST only")
    user = get_object_or_404(User, pk=pk)
    new_role = request.POST.get("role", "lecturer")
    if new_role not in {"lecturer", "admin"}:
        return HttpResponseBadRequest("invalid role")
    user.role = new_role
    user.save()
    return redirect("admin_users")


# ── Blackouts CRUD ───────────────────────────────────────────────────────────


@admin_required
def blackout_list(request):
    items = Blackout.objects.all().order_by("-date_start")
    return render(request, "AdminApp/blackouts.html", {"items": items})


@admin_required
def blackout_form(request):
    if request.method == "POST":
        form = BlackoutForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("admin_blackouts")
    else:
        form = BlackoutForm()
    return render(request, "AdminApp/blackout_form.html", {"form": form})


@admin_required
def blackout_delete(request, pk):
    if request.method != "POST":
        return HttpResponseBadRequest("POST only")
    blackout = get_object_or_404(Blackout, pk=pk)
    blackout.delete()
    return redirect("admin_blackouts")


# ── Reports ──────────────────────────────────────────────────────────────────


@admin_required
def report(request):
    rows = _report_rows()
    return render(request, "AdminApp/report.html", {"rows": rows})


@admin_required
def report_csv(request):
    response = HttpResponse(content_type="text/csv")
    stamp = datetime.now().strftime("%Y%m%d_%H%M")
    response["Content-Disposition"] = f'attachment; filename="tu_booking_report_{stamp}.csv"'
    writer = csv.writer(response)
    writer.writerow(
        ["room_id", "room_name", "subject_count", "tutoring_count", "total_hours"]
    )
    for row in _report_rows():
        writer.writerow(
            [
                row["room_id"],
                row["room_name"],
                row["subject_count"],
                row["tutoring_count"],
                row["total_hours"],
            ]
        )
    return response


def _report_rows():
    """Aggregate per-room booking stats for approved bookings."""
    rooms = Room.objects.all().order_by("room_id")
    rows = []
    for room in rooms:
        subj_qs = BookingForSubject.objects.filter(room=room, status="approved")
        tut_qs = BookingForTutoring.objects.filter(room=room, status="approved")
        total_hours = sum(_hours_for(b) for b in subj_qs) + sum(
            _hours_for(b) for b in tut_qs
        )
        rows.append(
            {
                "room_id": room.room_id,
                "room_name": room.room_name,
                "subject_count": subj_qs.count(),
                "tutoring_count": tut_qs.count(),
                "total_hours": round(total_hours, 1),
            }
        )
    return rows


def _hours_for(booking):
    """Approximate hours: per-day duration × number of matching weekdays in range."""
    from Bookingapp.utils import ALL_DAYS_ORDERED, range_to_days_list

    selected = set(range_to_days_list(booking.days_of_week))
    if not selected:
        return 0.0
    start = datetime.combine(date.today(), booking.time_start)
    end = datetime.combine(date.today(), booking.time_end)
    hours_per_day = max((end - start).total_seconds() / 3600.0, 0.0)

    occurrences = 0
    cur = booking.date_start
    while cur <= booking.date_end:
        if ALL_DAYS_ORDERED[cur.weekday()] in selected:
            occurrences += 1
        cur += timedelta(days=1)
    return hours_per_day * occurrences
