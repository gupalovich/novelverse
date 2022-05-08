import json
import uuid
import traceback

from django.db.models import F
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django_celery_beat.models import PeriodicTask, IntervalSchedule

from .models import Book, BookChapter
# from .tasks import book_scraper_info, book_scraper_chaps


@receiver(post_save, sender=Book)
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
    try:
        if created:
            instance.book.update_chapters_count()
            instance.c_id = instance.book.chapters_count
            instance.save(update_fields=['c_id'])
    except Exception as e:
        with open('error_log.txt', 'a', encoding='utf-8') as f:
            f.write(traceback.format_exc(e) + '\n')


@receiver(post_delete, sender=BookChapter)
def delete_update_chapter_cid(sender, instance, **kwargs):
    try:
        instance.book.update_chapters_count()
        c_id_del = instance.c_id
        book_chaps = BookChapter.objects.filter(book__slug=instance.book.slug).filter(c_id__gt=c_id_del)
        book_chaps.update(c_id=F('c_id') - 1)
    except Exception as e:
        with open('error_log.txt', 'a', encoding='utf-8') as f:
            f.write(traceback.format_exc(e) + '\n')
