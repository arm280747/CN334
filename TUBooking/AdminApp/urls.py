from django.urls import path

from . import views

urlpatterns = [
    path("admin-panel/", views.dashboard, name="admin_dashboard"),
    path("admin-panel/pending/", views.pending_list, name="admin_pending"),
    path(
        "admin-panel/pending/<str:kind>/<int:pk>/approve/",
        views.approve,
        name="admin_approve",
    ),
    path(
        "admin-panel/pending/<str:kind>/<int:pk>/reject/",
        views.reject,
        name="admin_reject",
    ),
    path("admin-panel/rooms/", views.room_list, name="admin_rooms"),
    path("admin-panel/rooms/new/", views.room_form, name="admin_room_new"),
    path("admin-panel/rooms/<int:pk>/edit/", views.room_form, name="admin_room_edit"),
    path(
        "admin-panel/rooms/<int:pk>/toggle/",
        views.room_disable,
        name="admin_room_toggle",
    ),
    path("admin-panel/users/", views.user_list, name="admin_users"),
    path(
        "admin-panel/users/<int:pk>/role/",
        views.user_set_role,
        name="admin_user_role",
    ),
    path("admin-panel/blackouts/", views.blackout_list, name="admin_blackouts"),
    path(
        "admin-panel/blackouts/new/",
        views.blackout_form,
        name="admin_blackout_new",
    ),
    path(
        "admin-panel/blackouts/<int:pk>/delete/",
        views.blackout_delete,
        name="admin_blackout_delete",
    ),
    path("admin-panel/report/", views.report, name="admin_report"),
    path("admin-panel/report/csv/", views.report_csv, name="admin_report_csv"),
]
