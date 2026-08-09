from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from apps.flights.models import Flight


class Command(BaseCommand):
    help = '删除到达超过 1 天的航班'

    def handle(self, *args, **options):
        cutoff = timezone.now() - timedelta(days=1)
        flights = Flight.objects.filter(
            status='arrived',
            status_changed_at__lte=cutoff
        )
        count = flights.count()
        flights.delete()
        self.stdout.write(f'已清理 {count} 个已到达航班')
