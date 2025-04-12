from django.core.management.base import BaseCommand
from ...tasks import start_scheduler
import time

class Command(BaseCommand):
    help = "Starts the APScheduler"

    def handle(self, *args, **kwargs):
        self.stdout.write("Starting scheduler...")
        start_scheduler()

        while True:
            time.sleep(60)