import os
import traceback
from celery import Celery, Task, states
from celery.exceptions import Ignore
from django.apps import apps, AppConfig
from django.conf import settings

from novel.settings.config.celery_app import app as celery_app


# if not settings.configured:
#     # set the default Django settings module for the 'celery' program.
#     os.environ.setdefault(
#         "DJANGO_SETTINGS_MODULE", "config.settings.local"
#     )  # pragma: no cover


# app = Celery("novelverse")
# # Using a string here means the worker will not have to
# # pickle the object when using Windows.
# # - namespace='CELERY' means all celery-related configuration keys
# #   should have a `CELERY_` prefix.
# app.config_from_object("django.conf:settings", namespace="CELERY")
# # app.conf.broker_transport_options = {"visibility_timeout": max_timeout_in_seconds}


# class CeleryAppConfig(AppConfig):
#     name = "novel.taskapp"
#     verbose_name = "Celery Config"

#     def ready(self):
#         installed_apps = [app_config.name for app_config in apps.get_app_configs()]
#         app.autodiscover_tasks(lambda: installed_apps, force=True)


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


