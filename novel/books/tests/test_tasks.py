from celery import states
from django.test import TestCase
from django_celery_results.models import TaskResult

from ..utils import save_celery_result
from ..tasks import clean_oneoff_tasks, clean_success_result_tasks


class BookTasksTest(TestCase):
    def setUp(self):
        pass

    def test_save_celery_result(self):
        save_celery_result(task_id='1', task_name='test task', status=states.SUCCESS)
        results = TaskResult.objects.all()
        self.assertEqual(results.count(), 1)
        results = results.first()
        self.assertEqual(results.task_id, '1')
        self.assertEqual(results.task_name, 'test task')

    def test_clean_oneoff_tasks(self):
        save_celery_result(task_id='1', task_name='test task 1', status=states.SUCCESS)
        save_celery_result(task_id='2', task_name='test task 2', status=states.SUCCESS)
        save_celery_result(task_id='3', task_name='test task 3', status=states.SUCCESS)

        results = TaskResult.objects.all()
        self.assertEqual(len(results), 3)
        clean_success_result_tasks.apply()
        results = TaskResult.objects.all()
        self.assertEqual(len(results), 0)
