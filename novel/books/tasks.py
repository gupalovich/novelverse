import traceback

from celery import Celery, Task, states
from celery.exceptions import Ignore
from config.celery_app import app as celery_app

from .utils import save_celery_result


@celery_app.task(bind=True, ignore_result=True)
def clean_oneoff_tasks(self):
    try:
        from django_celery_beat.models import PeriodicTask
        PeriodicTask.objects.filter(one_off=True, enabled=False).delete()
    except Exception as exc:
        save_celery_result(
            task_id=self.request.id,
            task_name=self.name,
            status=states.FAILURE,
            result=exc,
            traceback=traceback.format_exc(),
        )
        raise Ignore()


@celery_app.task(bind=True, ignore_result=True)
def clean_success_result_tasks(self):
    try:
        from django_celery_results.models import TaskResult
        TaskResult.objects.filter(status='SUCCESS').delete()
    except Exception as exc:
        save_celery_result(
            task_id=self.request.id,
            task_name=self.name,
            status=states.FAILURE,
            result=exc,
            traceback=traceback.format_exc(),
        )
        raise Ignore()
