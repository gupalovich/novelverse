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
from novel2read.apps.books.tasks import update_book_revisited, book_scraper_chaps_update, book_revisit_novel


class TaskRunner(TaskRunner):
    def run(self):
        tasks_qs = self.get_periodic_tasks()
        for task in tasks_qs:
            try:
                task_name = task.task.split('.')[-1]
                if task_name == 'update_book_revisited':
                    update_book_revisited.apply()
                elif task_name == 'book_scraper_chaps_update':
                    book_scraper_chaps_update.apply()
                    tasks_qs = self.get_periodic_tasks()
                    for task in tasks_qs:
                        task_name = task.task.split('.')[-1]
                        task_args = task.args.replace('[', '').replace(']', '').split(',')
                        if task_name == 'book_revisit_novel':
                            book_id = int(task_args[0])
                            book_revisit_novel.apply((book_id, ))
                            task.enabled = False
                            task.save(update_fields=['enabled'])
            except Ignore:
                task.enabled = False
                task.save(update_fields=['enabled'])


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(name)-24s: %(levelname)-8s %(message)s')

    task_runner = TaskRunner()
    task_runner.run()
