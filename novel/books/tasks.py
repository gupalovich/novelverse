import traceback

from celery import states
from celery.exceptions import Ignore
from django_celery_beat.models import PeriodicTask

from config.celery_app import app as celery_app
from .models import Book
from .scrapers import BookScraper
from .utils import save_celery_result, model_utils


@celery_app.task(bind=True, ignore_result=True)
def clean_oneoff_tasks(self):
    """Clean oneoff tasks with enabled=False"""
    try:
        PeriodicTask.objects.filter(one_off=True, enabled=False).delete()
    except Exception as e:
        save_celery_result(
            task_id=self.request.id,
            task_name=self.name,
            status=states.FAILURE,
            result=e,
            traceback=traceback.format_exc(),
        )
        raise Ignore()


@celery_app.task(bind=True, ignore_result=True)
def clean_success_result_tasks(self):
    try:
        from django_celery_results.models import TaskResult
        TaskResult.objects.filter(status='SUCCESS').delete()
    except Exception as e:
        save_celery_result(
            task_id=self.request.id,
            task_name=self.name,
            status=states.FAILURE,
            result=e,
            traceback=traceback.format_exc(),
        )
        raise Ignore()


@celery_app.task(bind=True)
def scrape_book_info_task(self, book_id):
    """Scrape initial info about the book from webnovel(default)"""
    try:
        book = Book.objects.get(pk=book_id)
        book_scraper = BookScraper()
        if book.visit == 'webnovel':
            book_url = book_scraper.urls[book.visit] + book.visit_id
            book_data = book_scraper.webnovel_get_book_data(book_url)
            model_utils.update_book_data(book, book_data)
        book.save()
    except Exception as e:
        save_celery_result(
            task_id=self.request.id,
            task_name=self.name,
            status=states.FAILURE,
            result=e,
            traceback=traceback.format_exc(),
        )
        raise Ignore()


@celery_app.task(bind=True, ignore_result=True)
def scrape_book_chapters_task(self, book_id):
    pass
