from django.contrib import admin

from NodeDB.models import DeviceMetrics, MeshNode, MeshUser, Position


@admin.register(MeshNode)
class MeshNodeAdmin(admin.ModelAdmin):
    list_display = ("id_str", "macaddr", "hw_model", "public_key")


@admin.register(MeshUser)
class MeshUserAdmin(admin.ModelAdmin):
    list_display = ("node", "long_name", "short_name")


@admin.register(Position)
class PositionAdmin(admin.ModelAdmin):
    list_display = (
        "node",
        "logged_time",
        "latitude",
        "longitude",
        "altitude",
        "location_source",
    )


@admin.register(DeviceMetrics)
class DeviceMetricsAdmin(admin.ModelAdmin):
    list_display = (
        "node",
        "logged_time",
        "battery_level",
        "voltage",
        "channel_utilization",
        "air_util_tx",
        "uptime_seconds",
    )
