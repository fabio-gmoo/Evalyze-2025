from django.core.management.base import BaseCommand  # type: ignore
from django.contrib.auth.models import User  # type: ignore


class Command(BaseCommand):
    help = "Deletes a specific admin user"

    def add_arguments(self, parser):
        parser.add_argument("username", type=str)

    def handle(self, *args, **kwargs):
        username = kwargs["username"]
        try:
            user = User.objects.get(username=username)
            user.delete()
            self.stdout.write(
                self.style.SUCCESS(f"User {username} deleted successfully")
            )
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"User {username} not found"))
