from django.core.management.base import BaseCommand
from analytics.ml_utils import train_model

class Command(BaseCommand):
    help = "Train student risk prediction model"

    def handle(self, *args, **options):
        acc = train_model()
        self.stdout.write(self.style.SUCCESS(f"Model trained. Accuracy: {acc:.3f}"))
