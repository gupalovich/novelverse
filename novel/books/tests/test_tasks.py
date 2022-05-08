from celery import states
from django.test import TestCase
from django_celery_results.models import TaskResult
from django_celery_beat.models import PeriodicTask, IntervalSchedule

from ..utils import save_celery_result
from ..tasks import clean_oneoff_tasks, clean_success_result_tasks


class BookTasksTest(TestCase):
    def setUp(self):
        pass

    def test_clean_oneoff_tasks(self):
        schedule, created = IntervalSchedule.objects.get_or_create(
            every=10,
            period=IntervalSchedule.SECONDS,
        )
        PeriodicTask.objects.create(
            interval=schedule,
            name=f'task enabled',
            task=f'test task enabled',
            one_off=True,
            enabled=True)
        for i in range(3):
            PeriodicTask.objects.create(
                interval=schedule,
                name=f'task {i}',
                task=f'test task {i}',
                one_off=True,
                enabled=False)
        tasks = PeriodicTask.objects.filter(one_off=True)
        self.assertTrue(len(tasks) == 4)
        clean_oneoff_tasks.delay()
        tasks = PeriodicTask.objects.filter(one_off=True)
        self.assertTrue(len(tasks) == 1)  # only 'enabled' left

    def test_save_celery_result(self):
        save_celery_result(task_id='1', task_name='test task', status=states.SUCCESS)
        results = TaskResult.objects.all()
        self.assertEqual(results.count(), 1)
        results = results.first()
        self.assertEqual(results.task_id, '1')
        self.assertEqual(results.task_name, 'test task')

    def test_clean_success_result_tasks(self):
        for i in range(3):
            save_celery_result(task_id=str(i), task_name=f'test task {i}', status=states.SUCCESS)
        results = TaskResult.objects.all()
        self.assertEqual(len(results), 3)
        clean_success_result_tasks.delay()
        results = TaskResult.objects.all()
        self.assertEqual(len(results), 0)
