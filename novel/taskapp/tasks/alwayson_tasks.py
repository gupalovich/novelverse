import logging
import time
import sys
import os
import environ
import django


ROOT_DIR = environ.Path(__file__) - 4
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.production")
sys.path.append(str(ROOT_DIR))
django.setup()


from celery.exceptions import Ignore
from django.utils import timezone
from django_celery_beat.models import PeriodicTask
from novel2read.apps.books.tasks import book_scraper_info, book_scraper_chaps


class TaskRunner:
    def __init__(self):
        logging.info(f'Creating instance: {self.__class__.__name__}')

    def get_django_time_now(self):
        pass

    def get_periodic_tasks(self):
        tasks_qs = PeriodicTask.objects.filter(enabled=True).select_related('interval').order_by('interval__every')
        return tasks_qs

    def run(self):
        tasks_qs = self.get_periodic_tasks()

        for task in tasks_qs:
            try:
                task_name = task.task.split('.')[-1]
                task_args = task.args.replace('[', '').replace(']', '').split(',')
                if task_name == 'book_scraper_info':
                    book_id = int(task_args[0])
                    book_scraper_info.apply((book_id, ))
                    task.enabled = False
                    task.save(update_fields=['enabled'])
                elif task_name == 'book_scraper_chaps':
                    book_id = int(task_args[0])
                    book_scraper_chaps.apply((book_id, ))
                    task.enabled = False
                    task.save(update_fields=['enabled'])
            except Ignore:
                task.enabled = False
                task.save(update_fields=['enabled'])


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(name)-24s: %(levelname)-8s %(message)s')

    task_runner = TaskRunner()
    task_runner.run()
