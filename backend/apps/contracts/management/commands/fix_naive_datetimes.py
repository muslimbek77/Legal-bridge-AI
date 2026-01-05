from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.contracts.models import Contract


class Command(BaseCommand):
    help = "Normalize Contract datetime fields to timezone-aware (UTC)."

    def handle(self, *args, **options):
        fixed = 0
        qs = Contract.objects.all()
        for contract in qs.iterator():
            dirty = False
            # Normalize datetime fields if naive
            for field in ["created_at", "updated_at", "analyzed_at"]:
                dt = getattr(contract, field, None)
                if dt is not None and timezone.is_naive(dt):
                    setattr(contract, field, timezone.make_aware(dt, timezone.utc))
                    dirty = True
            if dirty:
                contract.save(update_fields=["created_at", "updated_at", "analyzed_at"])
                fixed += 1
        self.stdout.write(self.style.SUCCESS(f"Fixed {fixed} contracts"))
