from django.db import models


class MeshNode(models.Model):
    id = models.BigIntegerField(primary_key=True, null=False)
    id_str = models.CharField(max_length=9, null=False)
    macaddr = models.CharField(max_length=20, null=True, blank=True)
    hw_model = models.CharField(max_length=50, null=True, blank=True)
    public_key = models.CharField(max_length=64, null=True, blank=True)

    def __str__(self):
        if not self.user:
            return self.id_str

        return f"{self.user.short_name} [{self.id_str}]"


class MeshUser(models.Model):
    node = models.OneToOneField(MeshNode, on_delete=models.CASCADE, related_name="user")
    long_name = models.CharField(max_length=50)
    short_name = models.CharField(max_length=5)

    def __str__(self):
        return self.short_name


class Position(models.Model):
    node = models.ForeignKey(MeshNode, on_delete=models.CASCADE, related_name="position_list")
    logged_time = models.DateTimeField()
    reported_time = models.DateTimeField()
    latitude = models.FloatField()
    longitude = models.FloatField()
    altitude = models.FloatField()
    location_source = models.CharField(max_length=50, null=True, blank=True)

    def __str__(self):
        return f"{self.node.id} - {self.logged_time}"


class DeviceMetrics(models.Model):
    class Meta:
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
        return f"{self.node.id} - {self.logged_time}"
