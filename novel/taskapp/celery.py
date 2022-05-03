import os
import traceback
from celery import Celery, Task, states
from celery.exceptions import Ignore
from django.apps import apps, AppConfig
from django.conf import settings


if not settings.configured:
    # set the default Django settings module for the 'celery' program.
    os.environ.setdefault(
        "DJANGO_SETTINGS_MODULE", "config.settings.local"
    )  # pragma: no cover


app = Celery("novelverse")
# Using a string here means the worker will not have to
# pickle the object when using Windows.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object("django.conf:settings", namespace="CELERY")
# app.conf.broker_transport_options = {"visibility_timeout": max_timeout_in_seconds}


class CeleryAppConfig(AppConfig):
    name = "novel.taskapp"
    verbose_name = "Celery Config"

    def ready(self):
        installed_apps = [app_config.name for app_config in apps.get_app_configs()]
        app.autodiscover_tasks(lambda: installed_apps, force=True)


class RequestBaseTask(Task):
    def run(self, *args, **kwargs):
        # The body of the task executed by workers. Required.
        pass

    def on_success(self, retval, task_id, *args, **kwargs):
        # do something with usefull values as retval and task_id
        pass

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        # do something
        pass


def save_celery_result(*args, **kwargs):
    from django_celery_results.models import TaskResult
    try:
        TaskResult.objects.create(
            task_id=kwargs.get('task_id', ''),
            task_name=kwargs.get('task_name', ''),
            status=kwargs.get('status', ''),
            content_type=kwargs.get('content_type', 'application/json'),
            content_encoding=kwargs.get('content_encoding', 'utf-8'),
            result=kwargs.get('result', ''),
            meta=kwargs.get('meta', ''),
            traceback=kwargs.get('traceback', ''),
        )
    except Exception as e:
        raise e


@app.task(bind=True, ignore_result=True)
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


@app.task(bind=True, ignore_result=True)
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
