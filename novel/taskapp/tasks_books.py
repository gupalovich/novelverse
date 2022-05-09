import json
import traceback
from celery import states
from celery.exceptions import Ignore
from novel.taskapp.celery import app, save_celery_result
from django_celery_beat.models import PeriodicTask, IntervalSchedule

from .models import Book, BookChapter
from .utils import search_multiple_replace, get_unique_slug
from .scrapers import BookScraper


@app.task(bind=True)
def b_chap_search_multiple_replace(self):
    try:
        print('Starting search_multiple_replace')
        result = search_multiple_replace()
        print('Done search_multiple_replace')
        return result
    except Exception as exc:
        save_celery_result(
            task_id=self.request.id,
            task_name=self.name,
            status=states.FAILURE,
            result=exc,
            traceback=traceback.format_exc(),
        )
        raise Ignore()


@app.task(bind=True)
def update_bookchapter_title_slug(self):
    try:
        b_chaps = BookChapter.objects.order_by('pk')
        counter = 0
        for b_chap in b_chaps.iterator(chunk_size=1000):
            if len(b_chap.title) >= 145:
                b_chap.title = 'untitled'
                b_chap.slug = get_unique_slug(BookChapter, 'untitled')
                b_chap.save(update_fields=['title', 'slug'])
                counter += 1
            elif len(b_chap.slug) >= 145:
                b_chap.slug = get_unique_slug(BookChapter, 'untitled')
                b_chap.save(update_fields=['title', 'slug'])
                counter += 1
        result = f'Done checking long b_chap titles. Updated: {counter}'
        return result
    except Exception as exc:
        save_celery_result(
            task_id=self.request.id,
            task_name=self.name,
            status=states.FAILURE,
            result='\n'.join([f'BookChapter: {b_chap.c_id} {b_chap.title}', exc]),
            traceback=traceback.format_exc(),
        )
        raise Ignore()


@app.task(bind=True, ignore_result=True)
def update_book_ranking(self):
    try:
        books = Book.objects.published().order_by('-votes')
        for i, book in enumerate(books, start=1):
            book.ranking = i
            book.save(update_fields=['ranking'])
    except Exception as exc:
        save_celery_result(
            task_id=self.request.id,
            task_name=self.name,
            status=states.FAILURE,
            result=exc,
            traceback=traceback.format_exc(),
        )
        raise Ignore()


@app.task(bind=True, ignore_result=True)
def update_book_revisited(self):
    try:
        books = Book.objects.filter(status_release=0)
        books.update(revisited=False)
    except Exception as exc:
        save_celery_result(
            task_id=self.request.id,
            task_name=self.name,
            status=states.FAILURE,
            result=exc,
            traceback=traceback.format_exc(),
        )
        raise Ignore()


@app.task(bind=True, ignore_result=True)
def book_scraper_info(self, book_id):
    """
        When new novel created - task initialised
    """
    book = Book.objects.get(pk=book_id)
    if not book.visited and book.visit_id:
        try:
            scraper = BookScraper()
            url_bb = scraper.url_bb[book.visit]
            book_url = f'{url_bb}{book.visit_id}'
            if book.visit == 'webnovel':
                book_data = scraper.wn_get_book_data(book_url)
                scraper.update_db_book_data(book, book_data)
            book.visited = True
            book.status = 1
            book.save()
        except Exception as exc:
            save_celery_result(
                task_id=self.request.id,
                task_name=self.name,
                status=states.FAILURE,
                result='\n'.join([f'Book: {book.title}', str(exc)]),
                traceback=traceback.format_exc(),
            )
            raise Ignore()
    else:
        raise Ignore()


@app.task(bind=True)
def book_scraper_chaps(self, book_id, s_from=0, s_to=0):
    """
        When new novel created - task initialised
    """
    book = Book.objects.get(pk=book_id)
    if book.visited and book.visit_id:
        try:
            scraper = BookScraper()
            book_url = f'{scraper.url_bb[book.visit]}{book.visit_id}'
            b_chap_info = None
            if book.visit == 'webnovel':
                c_ids = scraper.wn_get_book_cids(book_url)
                c_ids = c_ids[s_from:s_to] if s_to else c_ids[s_from:]
                b_chap_info = scraper.wn_get_update_book_chaps(book, book_url, c_ids)
            elif book.visit == 'gravitytails':
                c_ids = scraper.gt_get_book_cids(book_url)
                c_ids = c_ids[s_from:s_to] if s_to else c_ids[s_from:]
                b_chap_info = scraper.gt_get_update_book_chaps(book, book_url, c_ids)
            b_result = ' - '.join([f'{k}: {v},' for k, v in b_chap_info.items()])
            return b_result
        except Exception as exc:
            exc_result = '\n'.join([f'Book: {book.title}', f'{exc}'])
            save_celery_result(
                task_id=self.request.id,
                task_name=self.name,
                status=states.FAILURE,
                result=exc_result,
                traceback=traceback.format_exc(),
            )
            raise Ignore()
    else:
        raise Ignore()


@app.task(bind=True, ignore_result=True)
def book_revisit_novel(self, book_id, s_from=0, s_to=0):
    """
        TODO: If chap_release == 0: update on certain days
    """
    try:
        scraper = BookScraper()
        book = Book.objects.get(pk=book_id)
        book_url = f'{scraper.url_bb[book.revisit]}{book.revisit_id}'
        b_result = None

        if book.revisit == 'webnovel':
            c_ids = scraper.wn_get_book_cids(book_url, s_from=s_from, s_to=s_to)
            b_chap_info = scraper.wn_get_update_book_chaps(book, book_url, c_ids)
            b_result = ' - '.join([f'{k}: {v},' for k, v in b_chap_info.items()])
        elif book.revisit == 'gravitytails':
            c_ids = scraper.gt_get_book_cids(book_url, s_from=s_from, s_to=s_to)
            b_chap_info = scraper.gt_get_update_book_chaps(book, book_url, c_ids)
            b_result = ' - '.join([f'{k}: {v},' for k, v in b_chap_info.items()])
        elif book.revisit == 'boxnovel':
            b_chap_info = scraper.bn_get_update_book_chaps(book, book_url, s_to=s_to)
            b_result = f"""
                Updated book: {book.title};
                Updated len: {b_chap_info['updated']}
                Updated last: {b_chap_info['last']}
            """
        return b_result
    except Exception as exc:
        exc_result = '\n'.join([f'Book: {book.title}', f'{exc}'])
        save_celery_result(
            task_id=self.request.id,
            task_name=self.name,
            status=states.FAILURE,
            result=exc_result,
            traceback=traceback.format_exc(),
        )
        raise Ignore()


@app.task(bind=True, ignore_result=True)
def book_scraper_chaps_update(self, s_from=0, s_to=0):
    """
        Create update task for each novel with revisit=True
    """
    books = Book.objects.filter(visited=True).exclude(visit_id__iexact='').order_by('pk')
    interval = 15
    for book in books:
        if book.chapters_count and book.revisit_id and not book.revisited:
            try:
                interval += 3
                book.revisited = True
                book.save()
                schedule, created = IntervalSchedule.objects.get_or_create(
                    every=interval,
                    period=IntervalSchedule.SECONDS,
                )
                PeriodicTask.objects.create(
                    one_off=True,
                    interval=schedule,
                    name=f'Update book chapters: {book.title}',
                    task='novel.books.tasks.book_revisit_novel',
                    args=json.dumps([book.pk]),
                    kwargs=json.dumps({
                        's_from': s_from,
                        's_to': s_to,
                    }),
                )
            except Exception as exc:
                exc_result = '\n'.join([f'Book: {book.title}', f'{exc}'])
                save_celery_result(
                    task_id=self.request.id,
                    task_name=self.name,
                    status=states.FAILURE,
                    result=exc_result,
                    traceback=traceback.format_exc(),
                )
                raise Ignore()
