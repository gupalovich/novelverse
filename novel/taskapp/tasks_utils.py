# from novel.config.celery_app import app as celery_app


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
