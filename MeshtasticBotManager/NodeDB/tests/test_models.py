from django.test import TestCase
from django.utils import timezone

from ..models import DeviceMetrics, MeshNode, MeshUser, Position


class MeshNodeTest(TestCase):
    def setUp(self):
        self.node = MeshNode.objects.create(
            id=123456789,
            id_str="123456789",
            macaddr="00:11:22:33:44:55",
            hw_model="TBEAM",
            public_key="abc123",
        )

    def test_mesh_node_creation(self):
        self.assertEqual(self.node.id, 123456789)
        self.assertEqual(self.node.id_str, "123456789")
        self.assertEqual(self.node.macaddr, "00:11:22:33:44:55")
        self.assertEqual(self.node.hw_model, "TBEAM")
        self.assertEqual(self.node.public_key, "abc123")

    def test_mesh_node_str_without_user(self):
        self.assertEqual(str(self.node), "123456789")

    def test_mesh_node_str_with_user(self):
        MeshUser.objects.create(
            node=self.node,
            long_name="Test User",
            short_name="TEST",
        )
        self.assertEqual(str(self.node), "TEST [123456789]")


class MeshUserTest(TestCase):
    def setUp(self):
        self.node = MeshNode.objects.create(
            id=123456789,
            id_str="123456789",
        )
        self.user = MeshUser.objects.create(
            node=self.node,
            long_name="Test User",
            short_name="TEST",
        )

    def test_mesh_user_creation(self):
        self.assertEqual(self.user.long_name, "Test User")
        self.assertEqual(self.user.short_name, "TEST")
        self.assertEqual(self.user.node, self.node)

    def test_mesh_user_str(self):
        self.assertEqual(str(self.user), "TEST")


class PositionTest(TestCase):
    def setUp(self):
        self.node = MeshNode.objects.create(
            id=123456789,
            id_str="123456789",
        )
        self.now = timezone.now()
        self.position = Position.objects.create(
            node=self.node,
            logged_time=self.now,
            reported_time=self.now,
            latitude=51.5074,
            longitude=-0.1278,
            altitude=10.5,
            location_source="GPS",
        )

    def test_position_creation(self):
        self.assertEqual(self.position.node, self.node)
        self.assertEqual(self.position.latitude, 51.5074)
        self.assertEqual(self.position.longitude, -0.1278)
        self.assertEqual(self.position.altitude, 10.5)
        self.assertEqual(self.position.location_source, "GPS")

    def test_position_str(self):
        expected_str = f"{self.node.id} - {self.now}"
        self.assertEqual(str(self.position), expected_str)


class DeviceMetricsTest(TestCase):
    def setUp(self):
        self.node = MeshNode.objects.create(
            id=123456789,
            id_str="123456789",
        )
        self.now = timezone.now()
        self.metrics = DeviceMetrics.objects.create(
            node=self.node,
            logged_time=self.now,
            battery_level=85,
            voltage=3.7,
            channel_utilization=0.5,
            air_util_tx=0.3,
            uptime_seconds=3600,
        )

    def test_device_metrics_creation(self):
        self.assertEqual(self.metrics.node, self.node)
        self.assertEqual(self.metrics.battery_level, 85)
        self.assertEqual(self.metrics.voltage, 3.7)
        self.assertEqual(self.metrics.channel_utilization, 0.5)
        self.assertEqual(self.metrics.air_util_tx, 0.3)
        self.assertEqual(self.metrics.uptime_seconds, 3600)

    def test_device_metrics_str(self):
        expected_str = f"{self.node.id} - {self.now}"
        self.assertEqual(str(self.metrics), expected_str)
