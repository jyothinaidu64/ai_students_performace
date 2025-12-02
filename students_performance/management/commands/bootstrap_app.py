import os
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.conf import settings

User = get_user_model()


class Command(BaseCommand):
    help = (
        "Bootstrap app automatically in Render free tier.\n"
        "- Creates superuser if missing\n"
        "- Seeds demo data if missing\n"
        "- Creates media/ folder if missing"
    )

    def handle(self, *args, **kwargs):

        self.stdout.write("Running bootstrap steps...")

        # ------------------------------------------------------------
        # 1. Create media directory (in project root)
        # ------------------------------------------------------------
        media_dir = os.path.join(settings.BASE_DIR, "media")
        if not os.path.exists(media_dir):
            os.makedirs(media_dir)
            self.stdout.write(self.style.SUCCESS(f"Created media directory at: {media_dir}"))
        else:
            self.stdout.write("Media directory already exists.")

        # ------------------------------------------------------------
        # 2. Create default superuser
        # ------------------------------------------------------------
        username = "admin"
        password = "AdminPassword123"
        email = "admin@example.com"

        if not User.objects.filter(username=username).exists():
            User.objects.create_superuser(username=username, email=email, password=password)
            self.stdout.write(self.style.SUCCESS(f"Superuser '{username}' created."))
        else:
            self.stdout.write("Superuser already exists.")

        # ------------------------------------------------------------
        # 3. Seed demo data (ONLY if no schools exist)
        # ------------------------------------------------------------
        try:
            from schools.models import School
            if School.objects.count() == 0:
                self.stdout.write("Seeding demo data...")
                call_command("seed_demo_data")
                self.stdout.write(self.style.SUCCESS("Demo data seeded."))
            else:
                self.stdout.write("Demo data already present.")
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error seeding demo data: {e}"))

        self.stdout.write(self.style.SUCCESS("Bootstrap complete."))
