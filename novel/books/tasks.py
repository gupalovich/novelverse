import traceback
import logging
import json
import uuid

from celery import states
from celery.exceptions import Ignore
from django_celery_beat.models import PeriodicTask, IntervalSchedule
from selenium.common.exceptions import StaleElementReferenceException

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
    """TODO: Tests"""
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
    """TODO: Tests"""
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


@celery_app.task(bind=True)
def scrape_book_chapters_revisit_task(self, book_id):
    """Revisit external novel source if not revisited and revisit_id"""
    """TODO: Tests"""
    try:
        book = Book.objects.get(pk=book_id)
        book_scraper = BookScraper()
        if not book.revisit_id or book.revisited:
            return None
        if book.revisit == 'webnovel':
            pass
        elif book.revisit == 'pandanovel':
            """We get c_next from previously used chapter or none"""
            book_chap_url = book_scraper.panda_get_chap(book.revisit_id)['c_next']
            if not book_chap_url:
                return None
            stale_i = 0
            while True:
                try:
                    data = book_scraper.panda_get_chap(book_chap_url)
                except StaleElementReferenceException:
                    if stale_i >= 4:  # 4 attempts to get chapter
                        break
                    stale_i += 1
                    continue
                create_book_chapter(
                    book, data['c_id'], data['c_title'], data['c_content'],
                    origin=data['c_origin'], log=True)
                book.revisit_id = book_chap_url
                book.save(update_fields=['revisit_id'])
                if data['c_next']:
                    stale_i = 0
                    book_chap_url = data['c_next']
                else:
                    book.revisited = True
                    book.save(update_fields=['revisited'])
                    break
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
def update_book_revisited_task(self):
    """Update revisited field on books with status=0(ongoing)"""
    """TODO: Tests"""
    try:
        books = Book.objects.filter(status_release=0)  # ongoing novels
        books.update(revisited=False)
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
def add_book_revisit_tasks(self):
    """Filter books by revisited=False/revisit_id=True; Add task to revisit"""
    """TODO: Tests"""
    try:
        books = Book.objects.filter(revisited=False).exclude(revisit_id__iexact='')
        schedule, _ = IntervalSchedule.objects.get_or_create(
            every=15, period=IntervalSchedule.SECONDS)
        for book in books:
            if not book.chapters_count or not book.visited:
                continue
            salt = uuid.uuid4().hex[:12]
            PeriodicTask.objects.create(
                name=f'Revisit book chapters: {book.title} : {salt} ',
                task='novel.books.tasks.scrape_book_chapters_revisit_task',
                interval=schedule,
                enabled=True,
                one_off=True,
                args=json.dumps([book.pk]),
            )
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
def update_book_ranking_task(self):
    """TODO: Tests"""
    try:
        books = Book.objects.published().order_by('-votes')
        for i, book in enumerate(books, start=1):
            book.ranking = i
            book.save(update_fields=['ranking'])
    except Exception as e:
        save_celery_result(
            task_id=self.request.id,
            task_name=self.name,
            status=states.FAILURE,
            result=e,
            traceback=traceback.format_exc(),
        )
        raise Ignore()
