from django.apps import AppConfig
from django.db.utils import OperationalError, ProgrammingError

class OrderConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'order'


    def ready(self):
        try:
            from django_q.tasks import schedule
            from django_q.models import Schedule

            # Avoid creating duplicate schedules
            if not Schedule.objects.filter(func="order.tasks.cancel_expired_order").exists():
                schedule(
                    "order.tasks.cancel_expired_order",
                    schedule_type="I",  # interval
                    minutes=5,
                    repeats=-1,  # run forever
                )
        except (OperationalError, ProgrammingError):
            pass