"""Django management command to create and assign permissions for NodeDB models."""

from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand

from NodeDB.models import DeviceMetrics, MeshNode, MeshUser, Position


class Command(BaseCommand):
    """Command to create and assign permissions for NodeDB models to the Bots group."""

    help = "Create permissions for all models"

    def handle(self, *args, **kwargs):
        """Create permissions for each model and assign them to the Bots group."""
        models = [MeshNode, MeshUser, Position, DeviceMetrics]
        group, created = Group.objects.get_or_create(name="Bots")

        for model in models:
            content_type = ContentType.objects.get_for_model(model)
            permissions = [
                ("view", f"Can view {model.__name__}"),
                ("add", f"Can add {model.__name__}"),
                ("change", f"Can change {model.__name__}"),
            ]

            for codename, name in permissions:
                permission, created = Permission.objects.get_or_create(
                    codename=f"bots_{codename}_{model._meta.model_name}",
                    name=name,
                    content_type=content_type,
                )
                group.permissions.add(permission)

        self.stdout.write(self.style.SUCCESS("Successfully created permissions and assigned to group: Bots"))
