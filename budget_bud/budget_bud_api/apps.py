from django.apps import AppConfig
import threading
import time


class BudgetBudApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'budget_bud_api'

    def ready(self):
        time.sleep(2)

        from .tasks import start_scheduler
        threading.Thread(target=start_scheduler).start()