from django.core.management.base import BaseCommand
from analytics.ml_utils import train_next_score_models


class Command(BaseCommand):
    help = "Train per-subject next exam score prediction models."

    def handle(self, *args, **options):
        info = train_next_score_models()
        self.stdout.write(self.style.SUCCESS("Next-score models trained."))
        for s in info["subjects"]:
            self.stdout.write(
                f"Subject {s['subject_name']} ({s['subject_id']}): "
                f"samples={s['n_samples']}, train_R2={s['train_r2']:.3f}"
            )
