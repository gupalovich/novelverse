import logging
import sys
import os
import environ
import django

ROOT_DIR = environ.Path(__file__) - 4
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.production")
sys.path.append(str(ROOT_DIR))
django.setup()


from celery.exceptions import Ignore
from novel2read.taskapp.tasks.alwayson_tasks import TaskRunner
from novel2read.apps.books.tasks import update_book_ranking


class TaskRunner(TaskRunner):
    def run(self):
        tasks_qs = self.get_periodic_tasks()
        for task in tasks_qs:
            try:
                task_name = task.task.split('.')[-1]
                if task_name == 'update_book_ranking':
                    update_book_ranking.apply()
            except Ignore:
                task.enabled = False
                task.save(update_fields=['enabled'])


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(name)-24s: %(levelname)-8s %(message)s')

    task_runner = TaskRunner()
    task_runner.run()
