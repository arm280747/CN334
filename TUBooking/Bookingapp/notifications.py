"""Email notification helpers for booking lifecycle events.

Uses Django's send_mail under whatever EMAIL_BACKEND is configured
(defaults to console for dev). Failures are swallowed to never block a
booking save — a missing email shouldn't break the request flow.
"""

from django.conf import settings
from django.core.mail import send_mail

from .models import User


def _admin_recipients():
    """Combine User rows with role=admin and ADMIN_NOTIFY_EMAILS."""
    db_admins = list(
        User.objects.filter(role="admin")
        .exclude(email="")
        .values_list("email", flat=True)
    )
    extra = list(getattr(settings, "ADMIN_NOTIFY_EMAILS", []))
    return list(dict.fromkeys(db_admins + extra))


def _booking_summary(booking):
    return (
        f"ห้อง: {booking.room.room_name if booking.room else '-'}\n"
        f"ประเภท: {booking.get_booking_type_display()}\n"
        f"วันที่: {booking.date_start} – {booking.date_end}\n"
        f"วัน: {booking.days_of_week}\n"
        f"เวลา: {booking.time_start} – {booking.time_end}\n"
        f"ผู้จอง: {booking.display_name or booking.username}\n"
    )


def notify_admins_new_booking(booking):
    recipients = _admin_recipients()
    if not recipients:
        return
    subject = f"[TU Booking] คำขอจองใหม่: {booking.room.room_name if booking.room else '-'}"
    body = (
        "มีคำขอจองห้องเรียนใหม่รออนุมัติ\n\n"
        + _booking_summary(booking)
        + "\nกรุณาเข้าสู่ระบบเพื่อพิจารณาคำขอ"
    )
    _send(subject, body, recipients)


def notify_booker_status_change(booking):
    if not booking.email:
        return
    status_label = booking.get_status_display()
    subject = f"[TU Booking] สถานะการจองของคุณ: {status_label}"
    body = (
        f"สถานะการจองของคุณถูกอัปเดตเป็น: {status_label}\n\n"
        + _booking_summary(booking)
    )
    if booking.status == "rejected" and booking.denial_reason:
        body += f"\nเหตุผล: {booking.denial_reason}\n"
    _send(subject, body, [booking.email])


def _send(subject, body, recipients):
    try:
        send_mail(
            subject,
            body,
            settings.DEFAULT_FROM_EMAIL,
            recipients,
            fail_silently=True,
        )
    except Exception:
        # Never let an email failure break the surrounding request.
        pass
