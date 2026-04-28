"""AdminApp tests — model-level, no live HTTP or external API calls."""

from datetime import date, time, timedelta

from django.test import TestCase
from django.utils import timezone

from Bookingapp.models import Blackout, BookingForSubject, BookingForTutoring, Room, User
from Bookingapp.views import check_blackout_conflict, check_booking_conflict


def _make_room(room_id="TEST01"):
    return Room.objects.create(
        room_id=room_id,
        room_name="Test Room",
        room_capacity=30,
        room_info="",
        is_active=True,
    )


def _make_subject_booking(room, status="pending", **kwargs):
    defaults = dict(
        booking_type="subject",
        date_start=date.today(),
        date_end=date.today() + timedelta(days=7),
        days_of_week="จันทร์–ศุกร์",
        time_start=time(9, 0),
        time_end=time(11, 0),
        username="testuser",
        subject_code="CN334",
        subject_name="SE",
        curriculum="ปริญญาตรีภาคปกติ",
        status=status,
    )
    defaults.update(kwargs)
    return BookingForSubject.objects.create(room=room, **defaults)


class TestApproveWorkflow(TestCase):
    """approve() sets correct status and decision fields."""

    def test_approve_sets_status_and_decided_fields(self):
        room = _make_room()
        booking = _make_subject_booking(room, status="pending")
        booking.status = "approved"
        booking.decided_at = timezone.now()
        booking.decided_by = "admin01"
        booking.save()

        booking.refresh_from_db()
        self.assertEqual(booking.status, "approved")
        self.assertEqual(booking.decided_by, "admin01")
        self.assertIsNotNone(booking.decided_at)


class TestCancelBookingDateGuard(TestCase):
    """FR-BOOK-08: cancel_booking must refuse to cancel past bookings server-side."""

    def setUp(self):
        self.room = _make_room("CANCEL01")
        session = self.client.session
        session["username"] = "testuser"
        session["role"] = "lecturer"
        session.save()

    def _post_cancel(self, booking):
        return self.client.post(f"/booking/cancel/subject/{booking.pk}/")

    def test_cannot_cancel_past_booking(self):
        past = _make_subject_booking(
            self.room,
            status="approved",
            date_start=date.today() - timedelta(days=10),
            date_end=date.today() - timedelta(days=3),
        )
        self._post_cancel(past)
        past.refresh_from_db()
        self.assertEqual(past.status, "approved")   # unchanged

    def test_cannot_cancel_todays_booking(self):
        today_booking = _make_subject_booking(
            self.room,
            status="approved",
            date_start=date.today(),
            date_end=date.today() + timedelta(days=7),
        )
        self._post_cancel(today_booking)
        today_booking.refresh_from_db()
        self.assertEqual(today_booking.status, "approved")   # unchanged

    def test_can_cancel_future_booking(self):
        future = _make_subject_booking(
            self.room,
            status="approved",
            date_start=date.today() + timedelta(days=1),
            date_end=date.today() + timedelta(days=10),
        )
        self._post_cancel(future)
        future.refresh_from_db()
        self.assertEqual(future.status, "cancelled")

    def test_cannot_cancel_another_users_booking(self):
        other = _make_subject_booking(
            self.room,
            status="approved",
            date_start=date.today() + timedelta(days=3),
            date_end=date.today() + timedelta(days=10),
        )
        other.username = "someone_else"
        other.save()
        self._post_cancel(other)
        other.refresh_from_db()
        self.assertEqual(other.status, "approved")   # unchanged


class TestRejectWorkflow(TestCase):
    """reject() sets denial_reason and status=rejected."""

    def test_reject_requires_denial_reason(self):
        room = _make_room()
        booking = _make_subject_booking(room, status="pending")
        denial = "ห้องว่างไม่พอ"
        booking.status = "rejected"
        booking.denial_reason = denial
        booking.decided_at = timezone.now()
        booking.decided_by = "admin01"
        booking.save()

        booking.refresh_from_db()
        self.assertEqual(booking.status, "rejected")
        self.assertEqual(booking.denial_reason, denial)


class TestConflictIgnoresRejected(TestCase):
    """check_booking_conflict() must skip rejected/cancelled bookings."""

    def test_conflict_ignores_rejected_bookings(self):
        room = _make_room()
        # Create a rejected booking in the same slot
        _make_subject_booking(room, status="rejected")

        # A new booking in the same slot should NOT see a conflict
        conflicts = check_booking_conflict(
            room=room,
            date_start=date.today(),
            date_end=date.today() + timedelta(days=7),
            days_of_week="จันทร์–ศุกร์",
            time_start=time(9, 0),
            time_end=time(11, 0),
        )
        self.assertEqual(conflicts, [])

    def test_conflict_detected_for_pending(self):
        room = _make_room()
        _make_subject_booking(room, status="pending")

        conflicts = check_booking_conflict(
            room=room,
            date_start=date.today(),
            date_end=date.today() + timedelta(days=7),
            days_of_week="จันทร์–ศุกร์",
            time_start=time(9, 30),
            time_end=time(10, 30),
        )
        self.assertGreater(len(conflicts), 0)


class TestBlackoutBlocksBooking(TestCase):
    """check_blackout_conflict() returns blackouts overlapping requested range."""

    def test_blackout_blocks_booking(self):
        room = _make_room()
        Blackout.objects.create(
            room=room,
            date_start=date.today(),
            date_end=date.today() + timedelta(days=3),
            reason="ซ่อมแซม",
        )

        hits = check_blackout_conflict(
            room=room,
            date_start=date.today() + timedelta(days=1),
            date_end=date.today() + timedelta(days=2),
        )
        self.assertEqual(len(hits), 1)

    def test_global_blackout_blocks_any_room(self):
        room = _make_room()
        # null room = global blackout
        Blackout.objects.create(
            room=None,
            date_start=date.today(),
            date_end=date.today() + timedelta(days=2),
            reason="วันหยุด",
        )

        hits = check_blackout_conflict(
            room=room,
            date_start=date.today(),
            date_end=date.today() + timedelta(days=1),
        )
        self.assertEqual(len(hits), 1)


class TestAdminRequiredRedirect(TestCase):
    """admin_required decorator must redirect non-admin users."""

    def test_admin_required_redirects_lecturer(self):
        session = self.client.session
        session["username"] = "lecturer01"
        session["role"] = "lecturer"
        session.save()

        response = self.client.get("/admin-panel/")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/home/", response["Location"])

    def test_admin_required_redirects_unauthenticated(self):
        response = self.client.get("/admin-panel/")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login/", response["Location"])


class TestCsvExportColumns(TestCase):
    """report_csv returns a CSV with the expected header row."""

    def test_csv_export_returns_correct_columns(self):
        session = self.client.session
        session["username"] = "adminuser"
        session["role"] = "admin"
        session.save()

        response = self.client.get("/admin-panel/report/csv/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/csv")

        content = response.content.decode("utf-8")
        first_line = content.splitlines()[0]
        for col in ["room_id", "room_name", "subject_count", "tutoring_count", "total_hours"]:
            self.assertIn(col, first_line)
