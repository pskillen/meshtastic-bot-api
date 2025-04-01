"""Models for storing mesh network node information and associated data."""

from django.db import models


class MeshNode(models.Model):
    """Model representing a mesh network node."""

    id = models.BigIntegerField(primary_key=True, null=False)
    id_str = models.CharField(max_length=9, null=False)
    macaddr = models.CharField(max_length=20, null=True, blank=True)
    hw_model = models.CharField(max_length=50, null=True, blank=True)
    public_key = models.CharField(max_length=64, null=True, blank=True)

    def __str__(self):
        """Return a string representation of the node, including user's short name if available."""
        try:
            if self.user:
                return f"{self.user.short_name} [{self.id_str}]"
        except MeshNode.user.RelatedObjectDoesNotExist:
            pass
        return self.id_str


class MeshUser(models.Model):
    """Model representing a user associated with a mesh node."""

    node = models.OneToOneField(MeshNode, on_delete=models.CASCADE, related_name="user")
    long_name = models.CharField(max_length=50)
    short_name = models.CharField(max_length=5)

    def __str__(self):
        """Return the user's short name."""
        return self.short_name


class Position(models.Model):
    """Model representing a position report from a mesh node."""

    node = models.ForeignKey(MeshNode, on_delete=models.CASCADE, related_name="position_list")
    logged_time = models.DateTimeField()
    reported_time = models.DateTimeField()
    latitude = models.FloatField()
    longitude = models.FloatField()
    altitude = models.FloatField()
    location_source = models.CharField(max_length=50, null=True, blank=True)

    def __str__(self):
        """Return a string representation of the position report."""
        return f"{self.node.id} - {self.logged_time}"


class DeviceMetrics(models.Model):
    """Model representing device metrics reported by a mesh node."""

    class Meta:
        """Model metadata."""

        verbose_name = "Device metrics"
        verbose_name_plural = "Device metrics"

    node = models.ForeignKey(MeshNode, on_delete=models.CASCADE, related_name="device_metrics_list")
    logged_time = models.DateTimeField()
    battery_level = models.IntegerField()
    voltage = models.FloatField()
    channel_utilization = models.FloatField()
    air_util_tx = models.FloatField()
    uptime_seconds = models.IntegerField()

    def __str__(self):
        """Return a string representation of the device metrics report."""
        return f"{self.node.id} - {self.logged_time}"
