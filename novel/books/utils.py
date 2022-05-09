import os
import re
import requests
import traceback
import logging

from mimetypes import guess_extension
from django.core.exceptions import ImproperlyConfigured
from django.conf import settings
from django.utils.text import slugify


def download_img(url, file_name, folder='posters'):
    """Download bytes from url and save it to MEDIA_ROOT/folder"""
    url = f'https:{url}' if url[0:1] == '/' else url
    resp = requests.get(url)
    resp_type = resp.headers['content-type']
    if resp_type.partition('/')[0].strip() == 'image':
        file_ext = guess_extension(resp_type)
        file_ext = '.jpg' if file_ext == '.jpe' else file_ext
        file_path = os.path.join(settings.MEDIA_ROOT, folder)
        f_path = os.path.join(file_path, f'{file_name}{file_ext}')
        if not os.path.exists(file_path):
            os.makedirs(file_path)
        with open(f_path, 'wb') as f:
            f.write(resp.content)
        return f'{file_name}{file_ext}'
    else:
        raise ImproperlyConfigured


def upload_to_s3(file_name, bucket_path='', object_name=None, public_read=False):
    import boto3
    from botocore.exceptions import ClientError
    bucket = settings.AWS_STORAGE_BUCKET_NAME
    ACCESS_ID = settings.AWS_ACCESS_KEY_ID
    ACCESS_KEY = settings.AWS_SECRET_ACCESS_KEY

    if object_name is None:
        object_name = file_name.split('/')[-1].strip()
        print(object_name)

    s3_client = boto3.client('s3', aws_access_key_id=ACCESS_ID, aws_secret_access_key=ACCESS_KEY)

    try:
        if public_read:
            s3_client.upload_file(f'{file_name}', bucket, f'{bucket_path}/{object_name}', ExtraArgs={'ACL': 'public-read'})
        else:
            s3_client.upload_file(f'{file_name}', bucket, f'{bucket_path}/{object_name}')
    except ClientError as e:
        logging.error(e)
        return False
    return True


def save_celery_result(*args, **kwargs):
    from django_celery_results.models import TaskResult
    try:
        TaskResult.objects.create(
            task_id=kwargs.get('task_id', ''),
            task_name=kwargs.get('task_name', ''),
            status=kwargs.get('status', ''),
            content_type=kwargs.get('content_type', 'application/json'),
            content_encoding=kwargs.get('content_encoding', 'utf-8'),
            result=kwargs.get('result', ''),
            meta=kwargs.get('meta', ''),
            traceback=kwargs.get('traceback', ''),
        )
    except Exception as e:
        raise e


def get_unique_slug(cls, name):
    """TODO: other unicode(ru) slugify"""
    slug = slugify(name)
    unique_slug = slug
    num = 1
    while cls.objects.filter(slug=unique_slug).exists():
        unique_slug = '{}-{}'.format(slug, num)
        num += 1
    return unique_slug


def capitalize_str(string):
    return ' '.join([w.capitalize() for w in string.split(' ')])


def capitalize_slug(slug):
    return re.sub(r'\d', '', ' '.join([w.capitalize() for w in slug.split('-')])).strip()


def multiple_replace(to_repl, text):
    rep = dict((re.escape(k), v) for k, v in to_repl.items())
    pattern = re.compile("|".join(rep.keys()))
    text = pattern.sub(lambda m: rep[re.escape(m.group(0))], text)
    return text.strip()


def spoon_feed(qs, func, chunk=1000, start=0):
    """Split qs in chunks and do the `func` thing to them"""
    while start < qs.order_by('pk').last().pk:
        for o in qs.filter(pk__gt=start, pk__lte=start + chunk):
            yield func(o)
        start += chunk
        # gc.collect()


def handle_error(error, to_file=True):
    """TODO: add alternative to to_file(save it to task_results or smh else)"""
    if to_file:
        with open('error_log.txt', 'a', encoding='utf-8') as f:
            f.write(traceback.format_exc(error) + '\n\n')
    else:
        pass


class ModelUtils:
    def __init__(self):
        """Import as model_utils
           TODO: test all"""
        pass

    def filter_books_visit(self, qs, revisit=False):
        """Return QuerySet of filtered Books by visit/revisit column"""
        if revisit:
            books = qs.filter(visited=True).exclude(revisit_id__exact='')
        else:
            books = qs.filter(visited=False).exclude(visit_id__exact='')
        return books

    def create_book_tag(self, tag_name: str):
        """TODO: Check for book_tag similarity 85-90%"""
        from .models import BookTag
        slug_name = slugify(tag_name)
        tag = BookTag.objects.filter(slug=slug_name).exists()
        if not tag:
            logging.info(f'-- Creating tag: {tag_name}')
            booktag = BookTag.objects.create(name=tag_name)
            return booktag
        return False

    def create_book_chapter(self, book, c_id, title, text, thoughts='', origin=''):
        print(f'- Creating book_chapter: {title}')
        from .models import BookChapter
        bookchapter = BookChapter.objects.create(
            book=book, c_id=c_id, title=title, text=text, thoughts=thoughts, origin=origin)
        return bookchapter

    def add_book_booktag(self, book, tag_name: str):
        """Adds booktag to book if not exist"""
        try:
            from .models import Book, BookTag
            booktag = BookTag.objects.get(slug=slugify(tag_name))
            if booktag not in book.booktag.all():
                logging.info(f'- Adding: {tag_name}')
                book.booktag.add(booktag)
                return True
            return False
        except (BookTag.DoesNotExist, Book.DoesNotExist) as e:
            raise e

    def update_book_data(self, book, data: dict, save=False):
        """Update book object with scraped data"""
        print(f'- Updating book: {book}')
        book.title = data['book_title']
        book.title_sm = data['book_title_sm']
        book.author.append(data['book_author']) if data['book_author'] not in book.author else False
        book.description = data['book_description']
        if len(book.volumes) != len(data['book_volumes']):
            [book.volumes.append(volume) for volume in data['book_volumes']]
        poster_filename = download_img(data['book_poster_url'], slugify(data['book_title']))
        book.poster = f'posters/{poster_filename}'
        book.rating = data['book_rating']
        for tag in data['book_tags']:
            self.create_book_tag(tag)
            self.add_book_booktag(book, tag)
        book.visited = True
        book.status = 1
        if save:
            book.save()


model_utils = ModelUtils()
