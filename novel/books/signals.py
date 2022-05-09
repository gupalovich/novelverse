import json
import uuid

from django.db.models import F
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django_celery_beat.models import PeriodicTask, IntervalSchedule

from .models import Book, BookChapter
from .utils import handle_error
# from .tasks import book_scraper_info, book_scraper_chaps


@receiver(post_save, sender=Book)
def scrape_book_info_task_signal(sender, instance, created=False, **kwargs):
    """Update book info if not book.visited and book.visit_id; """
    try:
        if instance.visited or not instance.visit_id:  # no scrape url suplied
            return None
        salt = uuid.uuid4().hex[:12]
        schedule, _ = IntervalSchedule.objects.get_or_create(every=15, period=IntervalSchedule.SECONDS)
        PeriodicTask.objects.create(
            name=f'Update book: {instance.title} : {salt} ',
            task='novel.books.tasks.scrape_book_info_task',
            interval=schedule,
            enabled=True,
            one_off=True,
            args=json.dumps([instance.pk]),
        )
        if not instance.chapters_count:
            pass
    except Exception as e:
        handle_error(e)


# @receiver(post_save, sender=Book)
def book_scraper_initial_signal(sender, instance, created=False, **kwargs):
    """TODO: Error handling"""
    if not instance.visited and instance.visit_id:
        salt = uuid.uuid4().hex[:10]
        schedule, created = IntervalSchedule.objects.get_or_create(
            every=15,
            period=IntervalSchedule.SECONDS,
        )
        PeriodicTask.objects.create(
            one_off=True,
            interval=schedule,
            name=f'Update book: {instance.title}',
            task='novel.books.tasks.book_scraper_info',
            args=json.dumps([instance.pk]),
        )

        if not instance.chapters_count:
            schedule, created = IntervalSchedule.objects.get_or_create(
                every=50,
                period=IntervalSchedule.SECONDS,
            )
            PeriodicTask.objects.create(
                one_off=True,
                interval=schedule,
                name=f'Update book chapters init: {instance.title}',
                task='novel.books.tasks.book_scraper_chaps',
                args=json.dumps([instance.pk]),
            )


@receiver(post_save, sender=BookChapter)
def create_update_chapter_cid(sender, instance, created=False, **kwargs):
    """If new bookchapter created - update book.chapters_count and update bookchapter c_id"""
    try:
        if created:
            instance.book.update_chapters_count()
            instance.c_id = instance.book.chapters_count
            instance.save(update_fields=['c_id'])
    except Exception as e:
        handle_error(e)


@receiver(post_delete, sender=BookChapter)
def delete_update_chapter_cid(sender, instance, **kwargs):
    """If bookchapter deleted - update all chapters above deleted c_id"""
    try:
        instance.book.update_chapters_count()
        c_id_del = instance.c_id
        book_chaps = BookChapter.objects.filter(book__slug=instance.book.slug).filter(c_id__gt=c_id_del)
        book_chaps.update(c_id=F('c_id') - 1)
    except Exception as e:
        handle_error(e)
