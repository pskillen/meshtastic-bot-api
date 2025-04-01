"""Admin interface configuration for the NodeDB app."""

from django.contrib import admin

from NodeDB.models import DeviceMetrics, MeshNode, MeshUser, Position


@admin.register(MeshNode)
class MeshNodeAdmin(admin.ModelAdmin):
    """Admin interface for MeshNode model."""

    list_display = ("id_str", "macaddr", "hw_model", "public_key")


@admin.register(MeshUser)
class MeshUserAdmin(admin.ModelAdmin):
    """Admin interface for MeshUser model."""

    list_display = ("node", "long_name", "short_name")


@admin.register(Position)
class PositionAdmin(admin.ModelAdmin):
    """Admin interface for Position model."""

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
    """Admin interface for DeviceMetrics model."""

    list_display = (
        "node",
        "logged_time",
        "battery_level",
        "voltage",
        "channel_utilization",
        "air_util_tx",
        "uptime_seconds",
    )
