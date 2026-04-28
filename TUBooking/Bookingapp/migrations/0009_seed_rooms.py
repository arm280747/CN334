"""Data migration: seed the 5 default ECE rooms."""

from django.db import migrations


ROOMS = [
    {"room_id": "406-3",   "room_name": "ห้องประชุม 1", "room_capacity": 60, "room_info": "ห้องประชุม",  "is_active": True},
    {"room_id": "406-5",   "room_name": "ห้องประชุม 2", "room_capacity": 15, "room_info": "ห้องประชุม",  "is_active": True},
    {"room_id": "408-1",   "room_name": "ห้องประชุม 3", "room_capacity": 10, "room_info": "ห้องประชุม",  "is_active": True},
    {"room_id": "408-2/1", "room_name": "ห้องบรรยาย 1", "room_capacity": 20, "room_info": "ห้องเรียน",   "is_active": True},
    {"room_id": "408-2/2", "room_name": "ห้องบรรยาย 2", "room_capacity": 20, "room_info": "ห้องเรียน",   "is_active": True},
]


def seed_rooms(apps, schema_editor):
    Room = apps.get_model("Bookingapp", "Room")
    for data in ROOMS:
        Room.objects.get_or_create(room_id=data["room_id"], defaults=data)


def unseed_rooms(apps, schema_editor):
    Room = apps.get_model("Bookingapp", "Room")
    ids = [r["room_id"] for r in ROOMS]
    Room.objects.filter(room_id__in=ids).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("Bookingapp", "0008_bookingforsubject_created_at_and_more"),
    ]

    operations = [
        migrations.RunPython(seed_rooms, reverse_code=unseed_rooms),
    ]
