import os
import re
import requests
import logging

from mimetypes import guess_extension
from django.core.exceptions import ImproperlyConfigured
from django.conf import settings
from django.utils.text import slugify


def download_img(url, file_name):
    url = f'https:{url}' if url[0:1] == '/' else url
    resp = requests.get(url)
    resp_type = resp.headers['content-type']
    if resp_type.partition('/')[0].strip() == 'image':
        file_ext = guess_extension(resp_type)
        file_ext = '.jpg' if file_ext == '.jpe' else file_ext
        media_posters = os.path.join(settings.MEDIA_ROOT, 'posters')
        f_path = os.path.join(media_posters, f'{file_name}{file_ext}')
        if not os.path.exists(media_posters):
            os.makedirs(media_posters)
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
    string = ' '.join([w.capitalize() for w in string.split(' ')])
    return string


def capitalize_slug(slug):
    slug = re.sub('\d', '', ' '.join([w.capitalize() for w in slug.split('-')])).strip()
    return slug


def multiple_replace(to_repl, text):
    rep = dict((re.escape(k), v) for k, v in to_repl.items())
    pattern = re.compile("|".join(rep.keys()))
    text = pattern.sub(lambda m: rep[re.escape(m.group(0))], text)
    return text.strip()


def spoon_feed(qs, func, chunk=1000, start=0):
    while start < qs.order_by('pk').last().pk:
        for o in qs.filter(pk__gt=start, pk__lte=start + chunk):
            yield func(o)
        start += chunk
        # gc.collect()


def search_multiple_replace():
    from .models import BookChapter, BookChapterReplace
    b_chaps = BookChapter.objects.order_by('pk')
    to_repls = BookChapterReplace.objects.order_by('pk')
    result = []
    for b_chap in b_chaps.iterator(chunk_size=1000):
        if '<br>' in b_chap.text:
            b_chap_text = b_chap.text.split('<p>')
            new_text = []
            for text_node in b_chap_text:
                text_node = text_node.replace('<p>', '').replace('</p>', '')
                brs = text_node.split('<br>')
                [new_text.append(f'<p>{br}</p>') if br else '' for br in brs]
            b_chap.text = ''.join(new_text)
            b_chap.save(update_fields=['text'])
            result.append(f'{b_chap.book} - {b_chap.title}\n')
    # for b_chap in b_chaps:
    #     b_chap_text = re.sub('[^a-zA-Z]+', '', b_chap.text.lower())
    #     for k, v in to_repl.items():
    #         if k in b_chap_text:
    #             if 'boxnovel' in k:
    #                 rx_repl = r'.{0,1}\s{0,2}'.join(k)
    #             else:
    #                 rx_repl = k
    #             b_chap.text = re.sub(rx_repl, v, b_chap.text, flags=re.I)
    #             b_chap.save()

    return result
