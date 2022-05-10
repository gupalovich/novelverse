import traceback
import logging

from celery import states
from celery.exceptions import Ignore
from django_celery_beat.models import PeriodicTask

from config.celery_app import app as celery_app
from .models import Book
from .scrapers import BookScraper
from .utils import save_celery_result, update_book_data, create_book_chapter


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
        book_url = book_scraper.urls[book.visit] + book.visit_id
        if book.visit == 'webnovel':
            book_data = book_scraper.webnovel_get_book_data(book_url)
            update_book_data(book, book_data)
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
def scrape_initial_book_chapters_task(self, book_id):
    """Get book chap_ids - Create chapters until lock reached"""
    try:
        book = Book.objects.get(pk=book_id)
        if book.chapters_count:
            return None
        book_scraper = BookScraper()
        book_url = book_scraper.urls[book.visit] + book.visit_id
        if book.visit == 'webnovel':
            chap_ids = book_scraper.webnovel_get_chap_ids(book_url)
            for i, chap_id in enumerate(chap_ids):
                book_chap_url = f'{book_url}/{chap_id}'
                data = book_scraper.webnovel_get_chap(book_chap_url)
                if not data:
                    logging.info(f'- Chapters Lock reached at: {i}')
                    break
                create_book_chapter(
                    book, data['c_id'], data['c_title'], data['c_content'],
                    thoughts=data['c_thoughts'], origin=data['c_origin'], log=True)
    except Exception as e:
        save_celery_result(
            task_id=self.request.id,
            task_name=self.name,
            status=states.FAILURE,
            result=e,
            traceback=traceback.format_exc(),
        )
        raise Ignore()
