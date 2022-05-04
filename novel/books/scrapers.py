import logging
import re

from django.utils.text import slugify
from datetime import datetime
from requests_html import HTMLSession
from selenium import webdriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException
from fake_useragent import UserAgent

# from .models import Book, BookChapter, BookTag  # comment to execute '__main__'
# from .utils import *  # comment to execute '__main__'


class BookScraper:
    def __init__(self):
        self.urls = {
            'webnovel': 'https://www.webnovel.com/book/',
            'boxnovel': 'https://boxnovel.com/novel/',
            'pandanovel': 'https://www.panda-novel.com/',
        }
        self.driver_opts = webdriver.ChromeOptions()
        # self.driver_opts.add_argument('headless')
        self.driver_opts.add_argument('disable-gpu')
        self.driver_opts.add_argument('log-level=3')
        self.driver_opts.add_argument('lang=en-US')
        self.driver_opts.add_argument('silent')

    def setup_user_agent(self) -> None:
        user_agent = UserAgent()
        user_agent = user_agent.random
        self.driver_opts.add_argument(f'user-agent={user_agent}')

    def sel_find_css(self, driver, selector, many=False):
        if many:
            return driver.find_elements(by=By.CSS_SELECTOR, value=selector)
        else:
            return driver.find_element(by=By.CSS_SELECTOR, value=selector)

    def sel_wait_until(self, driver, selector, delay=5):
        wait = WebDriverWait(driver, delay)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))

    def webnovel_get_book_data(self, book_url: str) -> dict:
        """GET webnovel book data with html_requests"""
        session = HTMLSession()
        r = session.get(book_url)
        book = {}
        b_title_raw = r.html.find('h1.pt4')[0].text
        b_title = ' '.join(b_title_raw.split(' ')[0:-1])
        b_title_sm = r.html.find('h1.pt4 small')[0].text
        b_desc_raw = r.html.find('.j_synopsis')[0].text
        b_desc = ''.join([f'<p>{i}</p>' for i in b_desc_raw.split('\n') if i])
        b_tags = [tag.text.replace('# ', '').lower() for tag in r.html.find('p.m-tag')]
        try:
            b_author = r.html.find('h2.ell.dib.vam span')[0].text
        except IndexError:
            b_author = ''
        b_rating = float(r.html.find('._score.ell strong')[0].text)
        b_poster_url = r.html.find('i.g_thumb img')[1].attrs['src']
        book.update({
            'book_title': b_title,
            'book_title_sm': b_title_sm,
            'book_description': b_desc,
            'book_tags': b_tags,
            'book_author': b_author,
            'book_rating': b_rating,
            'book_poster_url': b_poster_url,
        })
        return book

    def webnovel_get_book_volumes(self, book_url: str) -> list:
        """GET webnovel book volumes with selenium"""
        # self.setup_user_agent()
        driver = webdriver.Chrome(options=self.driver_opts)
        driver.get(book_url)
        self.sel_find_css(driver, 'a.j_show_contents').click()
        self.sel_wait_until(driver, '.volume-item')
        volumes = self.sel_find_css(driver, '.volume-item', many=True)
        book_volumes = [1, ]
        for volume in volumes:
            chap_len = len(self.sel_find_css(driver, '.volume-item ol li', many=True))
            volume_len = len(self.sel_find_css(volume, 'ol li', many=True))
            volume_len += book_volumes[-1]
            if volume_len - 1 != chap_len:
                book_volumes.append(volume_len)
        driver.close()
        return book_volumes

    def webnovel_get_chap_ids(self, book_url: str, s_from=0, s_to=0) -> list:
        """GET webnovel book chapter ids with selenium"""
        # self.setup_user_agent()
        driver = webdriver.Chrome(options=self.driver_opts)
        driver.get(book_url)
        self.sel_find_css(driver, 'a.j_show_contents').click()
        self.sel_wait_until(driver, '.content-list')
        c_list = self.sel_find_css(driver, '.content-list li', many=True)
        if s_to:
            c_list = c_list[s_from:s_to]
        c_ids = [li.get_attribute("data-cid") for li in c_list]
        driver.close()
        return c_ids

    def webnovel_get_chap(self, chap_url: str) -> dict:
        """GET webnovel book chapter data and comments with selenium"""
        print(chap_url)
        driver = webdriver.Chrome(options=self.driver_opts)
        driver.get(chap_url)
        chap_data = {}
        try:
            self.sel_find_css(driver, '.cha-content._lock')
        except NoSuchElementException:
            chap_title_raw = self.sel_find_css(driver, '.cha-tit h1').text
            try:
                chap_title = re.split(
                    r':|-|–', chap_title_raw, maxsplit=1)[1].strip().replace('‽', '?!')
                chap_id = int(re.findall(r'\d+', chap_title_raw)[0])
            except IndexError:
                chap_title = chap_title_raw
                chap_id = 'info'
            chap_content_raw = self.sel_find_css(driver, '.cha-paragraph p', many=True)
            chap_content = ''.join([f'<p>{p.text}</p>' for p in chap_content_raw if p.text])
            chap_thoughts_raw = self.sel_find_css(driver, '.m-thou p', many=True)
            chap_thoughts = ''
            for p in chap_thoughts_raw:  # filter whatever 'thoughts' here
                p_text = p.text
                if not p_text or 'webnovel' in p_text:
                    continue
                chap_thoughts += f'<p>{p_text}</p>'
            self.sel_find_css(driver, 'a.j_comments').click()
            self.sel_wait_until(driver, '.m-comment-bd')
            chap_comments_raw = self.sel_find_css(driver, '.m-comment-bd', many=True)
            chap_commments = []
            for comment in chap_comments_raw:
                comment = re.sub(r'\[img=\w+\]', '', comment.text)
                if len(comment) > 3:
                    chap_commments.append(comment.capitalize())
            chap_data.update({
                'c_id': chap_id,
                'c_title': chap_title,
                'c_content': chap_content,
                'c_thoughts': chap_thoughts,
                'c_comments': chap_commments,
            })
        driver.close()
        return chap_data

    def panda_get_chap_ids(self, book_url: str) -> list:
        driver = webdriver.Chrome(options=self.driver_opts)
        driver.get(book_url)
        self.sel_wait_until(driver, '.chapter-list')
        chaps_raw = self.sel_find_css(driver, '.chapter-list ul li a', many=True)
        chaps = []
        for chap in chaps_raw:
            try:
                chap = chap.get_attribute('href')
                if not chap:
                    continue
                elif '/chapter-' in chap:
                    chaps.append(chap)
            except StaleElementReferenceException:
                continue
        return chaps

    def run(self):
        from pprint import pprint
        book_ids = ['blood-warlock-succubus-partner-in-the-apocalypse(IN)-1122', 'birth-of-the-demonic-sword(IN)-74']
        for b_id in book_ids:
            url = self.urls['pandanovel'] + 'details/' + b_id
            pprint(self.panda_get_chap_ids(url))


if __name__ == '__main__':
    logging.basicConfig(level=logging.WARNING, format='%(name)-24s: %(levelname)-8s %(message)s')
    start = datetime.now()

    scraper = BookScraper()
    scraper.run()

    finish = datetime.now() - start
    logging.info(f'Done in: {finish}')


class BookScraper2:
    def __init__(self):
        logging.info(f'Creating instance: {self.__class__.__name__}')
        self.url_bb = {
            'webnovel': 'https://www.webnovel.com/book/',
            'boxnovel': 'https://boxnovel.com/novel/',
            'wuxiaworld': 'https://www.wuxiaworld.com/novel/',
            'gravitytails': 'https://gravitytales.com/novel/',
            'lnmtl': 'https://lnmtl.com/novel/',
        }
        self.to_repl = {
            '<p>': '', '</p>': '', '<p/>': '',
            '<p style="line-height: 1.15">': '',
            '<p style="padding-left: 0; line-height: 1.15; padding-right: 0">': '',
            '<p dir="ltr">': '', '<p dir="rtr">': '',
            '<p style="text-align: center">': '',
            '<p style="text-align: center;">': '',
            '<p style="line-height: 1.5">': '',
            '<p style="line-height: 1.5;">': '',
            '<p style="text-align: center"/>': '',
            '<p style="line-height: 2.0">': '',
            '<p data-children-count="0">': '',
            '<p style="text-align: center;"/>': '',
            '<p style="padding-left: 0; line-height: 1.5; padding-right: 0">': '',
            '<p style="line-height: 1.5; text-align: justify"><span style="font-family: Arial, Helvetica, sans-serif">': '',
            '<strong>': '', '</strong>': '',
            '<span>': '', '</span>': '',
            '<span style="font-family: Arial, Helvetica, sans-serif">': '',
            '<span style="font-style: italic">': '',
            '<span style="font-style: italic;">': '',
            '<span style="font-weight: 700"/>': '',
            '<span style="font-weight: 400">': '',
            '<span style="font-weight: 400;">': '',
            '<span style="font-weight: 700">': '',
            '<span style="font-weight: 700;">': '',
            '<span style="font-size: 1.15em">': '',
            '<span style="font-family: Arial">': '',
            '<span class="spoiler">': '',
            '<br class="Apple-interchange-newline"/>': '',
            '<br class="kix-line-break">': '',
            '<br class="kix-line-break"/>': '',
            '<u>': '', '</u>': '',
            # '\u201d': '"', '\u201c': '"', "`": "'",
            # "\u2018": "'", "\u2019": "'",
            # '\u2013': ' - ', '\u2014': ' - ',
            '[]': '', '\xdc': 'U',
            '\u0304': '', '\u0305': '',
            '\u203d': '?!',
            '\uff01': '!',
            '\n': '', '\r': '',
            '\xa0': ' ',
        }
        self.to_repl_html = {
            '<div>': '', '</div>': '',
            '<div style="max-width: 100%; overflow: auto">': '',
            '<div style="max-width: 100%; overflow:auto">': '',
            '<div class="innerContent fr-view" id="chapterContent">': '',
            '<span>': '', '</span>': '', '<span/>': '',
            '<span style="color: #ff00ff">': '',
            '<span style="font-weight: 400">': '',
            '<span style="color: #999999">': '',
            '<u>': '', '</u>': '',
            '<td style="text-align: center">': '<td>',
            '<td style="text-align: center;">': '<td>',
            '<table border="1" cellpadding="0" cellspacing="0" dir="ltr">': '<table border="1" cellpadding="10" cellspacing="0" dir="ltr">',
            '<table style="background-color: #000000">': '<table border="1" cellpadding="10" cellspacing="0" dir="ltr">',
            '<table style="background-color: #000000;">': '<table border="1" cellpadding="10" cellspacing="0" dir="ltr">',
            '\n': '', '\r': '',
            '\xa0': ' ',
        }
        self.driver_opts = webdriver.ChromeOptions()
        self.driver_opts.add_argument('headless')
        self.driver_opts.add_argument('disable-gpu')
        self.driver_opts.add_argument('log-level=3')
        self.driver_opts.add_argument('silent')

    def raw_html_text_filter(self, html_text):
        if len(html_text) > 3:
            if not isinstance(html_text[0], str):
                if len(html_text[0].text) >= 1500:
                    del html_text[0]

        filtered_html_text = []
        for i, text_node in enumerate(html_text):
            text_node = text_node.html if not isinstance(html_text[0], str) else text_node
            node = multiple_replace(self.to_repl, text_node)
            # node = node.encode("ascii", errors="ignore").decode()

            if i <= 5 and node:
                if 'chapter' in node.lower():
                    node = ''
                elif 'episode' in node.lower():
                    node = ''
                elif node[0].isdigit():
                    node = ''
                elif 'ed:' in node.lower():
                    node = ''
                elif 'written by' in node.lower():
                    node = ''
                elif 'translator' in node.lower():
                    node = ''
                elif 'transator' in node.lower():
                    node = ''
                elif 'translated' in node.lower():
                    node = ''
                elif 'edited' in node.lower():
                    node = ''
                elif 'editor' in node.lower():
                    node = ''
                elif 'proofreader' in node.lower():
                    node = ''
                elif 'tl check' in node.lower():
                    node = ''
                elif 'TL' in node:
                    node = ''
                elif '<ol' in node.lower():
                    node = ''
                elif 'webnovel' in re.sub('[^a-zA-Z]+', '', node.lower()):
                    node = ''

            if node:
                if '<br/>' in node:
                    node_brs = node.split('<br/>')
                    for node in node_brs:
                        if node:
                            node = f'<p>{node.strip()}</p>'
                            filtered_html_text.append(node)
                elif '</a>' in node:
                    node = ''
                elif 'http' in node or 'https' in node:
                    node = ''
                elif 'www.' in node:
                    node = ''
                else:
                    node = f'<p>{node.strip()}</p>'
                    filtered_html_text.append(node)

        return filtered_html_text

    def raw_html_filter(self, html):
        html = multiple_replace(self.to_repl_html, html)
        return html

    def get_filter_db_books(self, qs, revisit=False):
        if revisit:
            books = qs.filter(visited=True).exclude(revisit_id__exact='')
        else:
            books = qs.filter(visited=False).exclude(visit_id__exact='')
        return books

    def create_book_tag(self, name):
        slug_name = slugify(name)
        tag = BookTag.objects.filter(slug=slug_name).exists()
        if not tag:
            logging.info(f'-- Creating tag: {name}')
            booktag = BookTag.objects.create(name=name)
            return booktag
        return False

    def add_book_booktag(self, book, tag_name):
        try:
            booktag = BookTag.objects.get(slug=slugify(tag_name))
            if booktag not in book.booktag.all():
                logging.info(f'-- Adding: {tag_name}')
                book.booktag.add(booktag)
                return True
            return False
        except (BookTag.DoesNotExist, Book.DoesNotExist) as e:
            raise e

    def update_db_book_data(self, book, data):
        print(f'Updating book: {book}')
        data = data[0] if isinstance(data, list) else data
        book.title = data['book_name']
        book.title_sm = data['book_name_sm']
        book.author.append(data['book_info_author']) if data['book_info_author'] not in book.author else False
        if len(book.description) < 100:
            book.description = data['book_desc']
        if len(book.volumes) != len(data['book_volumes']):
            [book.volumes.append(volume) for volume in data['book_volumes']]
        poster_filename = download_img(data['book_poster_url'], slugify(data['book_name']))
        book.poster = f'posters/{poster_filename}'
        s3_uploaded = upload_to_s3(f'novel2read/media/{book.poster}', bucket_path='media/posters', public_read=True)
        if s3_uploaded:
            print('Poster uploaded to s3')
        book.rating = data['book_rating']
        if data['chap_release'] == 'completed':
            book.status_release = 1
        elif isinstance(data['chap_release'], int):
            book.chapters_release = data['chap_release']
        for tag in data['book_tag_list']:
            self.create_book_tag(tag)
            self.add_book_booktag(book, tag)
        book.visited = True
        # book.save()  # prevent celery post_save closure

    def create_book_chapter(self, book, c_title, c_content):
        print(f'Creating: {c_title}')
        bookchapter = BookChapter.objects.create(book=book, title=c_title, text=c_content)
        return bookchapter

    def wn_get_book_data(self, book_url):
        driver = webdriver.Chrome(chrome_options=self.driver_opts)
        wait = WebDriverWait(driver, 5)
        driver.get(book_url)
        driver.find_element_by_css_selector('a.j_show_contents').click()
        v_list = wait.until(lambda driver: driver.find_elements_by_css_selector('.volume-item'))
        book_volumes = [1]
        for volume in v_list:
            chap_len = len(driver.find_elements_by_css_selector('.volume-item ol li'))
            volume_len = len(volume.find_elements_by_css_selector('ol li'))
            volume_len += book_volumes[-1]
            if volume_len - 1 != chap_len:
                book_volumes.append(volume_len)
        driver.close()

        session = HTMLSession()
        r = session.get(book_url)
        book_name_raw = r.html.find('.pt4.pb4.oh.mb4')[0].text
        book_name = ' '.join(book_name_raw.split(' ')[0:-1]).replace('‽', '?!')
        book_name_sm = book_name_raw.split(' ')[-1]
        chap_release_raw = r.html.find('.det-hd-detail strong')[0].text
        chap_release = chap_release_raw.lower().strip() if len(chap_release_raw) < 20 else int(re.findall('\d+', chap_release_raw)[0])
        book_info_chap_count_raw = r.html.find('.det-hd-detail strong')[1].text
        book_info_chap_count = int(re.findall('\d+', book_info_chap_count_raw)[0])
        book_info_author = r.html.find('.ell.dib.vam span')[0].text
        book_rating = float(r.html.find('._score.ell strong')[0].text)
        book_poster_url = ''.join(r.html.find('i.g_thumb img')[1].attrs['srcset'].split(' '))
        book_desc_raw = r.html.find('p.mb48.fs16.c_000')[0].html.split('<br/>')
        book_desc_raw = ['' if 'webnovel' in p.lower() else p for p in book_desc_raw]
        book_desc_raw = [multiple_replace(self.to_repl, p.strip()) for p in book_desc_raw]
        book_desc = ''.join([f"<p>{re.sub(r'<.*?>', '', text)}</p>" for text in book_desc_raw]).replace('<p></p>', '')
        book_tag_list = [a.text.strip() for a in r.html.find('.pop-tags a')]

        book = []
        book.append({
            'book_name': book_name,
            'book_name_sm': book_name_sm,
            'chap_release': chap_release,
            'book_info_chap_count': book_info_chap_count,
            'book_info_author': book_info_author,
            'book_volumes': book_volumes,
            'book_rating': book_rating,
            'book_poster_url': book_poster_url,
            'book_desc': book_desc,
            'book_tag_list': book_tag_list,
        })
        return book

    def wn_get_book_cids(self, book_url, s_from=0, s_to=0):
        driver = webdriver.Chrome(chrome_options=self.driver_opts)
        wait = WebDriverWait(driver, 5)
        driver.get(book_url)
        # DOM
        driver.find_element_by_css_selector('a.j_show_contents').click()
        if s_to:
            c_list = wait.until(lambda driver: driver.find_elements_by_css_selector('.content-list li')[s_from:s_to])
        else:
            c_list = wait.until(lambda driver: driver.find_elements_by_css_selector('.content-list li'))
        c_ids = [li.get_attribute("data-cid") for li in c_list]
        driver.close()
        return c_ids

    def wn_get_book_chap(self, chap_url):
        session = HTMLSession()
        r_chap = session.get(chap_url)
        print(chap_url)
        chap_tit_raw = r_chap.html.find('.cha-tit h3')[0].text
        chap_lock = r_chap.html.find('.cha-content._lock')

        if len(chap_lock) == 0:
            chap_tit = re.split(r':|-|–', chap_tit_raw, maxsplit=1)[1].strip().replace('‽', '?!')
            chap_tit_id = int(re.findall('\d+', chap_tit_raw)[0])

            chap_content_raw = r_chap.html.find('.cha-words p')
            chap_content_filtered = self.raw_html_text_filter(chap_content_raw)
            b_chap = {
                'c_id': chap_tit_id,
                'c_title': chap_tit,
                'c_content': ''.join(chap_content_filtered),
            }
            return b_chap
        return chap_tit_raw

    def wn_get_update_book_chaps(self, book, book_url, c_ids):
        b_chap_url = ''
        b_chap = ''
        for c_id in c_ids[book.chapters_count:]:
            b_chap_url = f'{book_url}/{c_id}'
            b_chap = self.wn_get_book_chap(b_chap_url)
            if isinstance(b_chap, dict):
                self.create_book_chapter(book, b_chap['c_title'], b_chap['c_content'])
            else:
                break
        b_chap = b_chap['c_title'] if isinstance(b_chap, dict) else b_chap
        b_chap_info = {
            'Source': 'webnovel',
            'locked_ended_from': b_chap,
            'locked_ended_from_url': b_chap_url,
        }
        return b_chap_info

    def bn_get_book_chap(self, chap_url):
        session = HTMLSession()
        r_chap = session.get(chap_url)

        h1_tit = r_chap.html.find('.reading-content h1')
        h2_tit = r_chap.html.find('.reading-content h2')
        h3_tit = r_chap.html.find('.reading-content h3')
        h4_tit = r_chap.html.find('.reading-content h4')
        chap_tit_raw = ''

        if h1_tit:
            chap_tit_raw = h1_tit[0].text
        elif h2_tit:
            chap_tit_raw = h2_tit[0].text
        elif h3_tit:
            chap_tit_raw = h3_tit[0].text
        elif h4_tit:
            chap_tit_raw = h4_tit[0].text
        else:
            nodes = r_chap.html.find('.reading-content p')[:5]
            if len(nodes) >= 4:
                for node in nodes:
                    text_node = node.text.lower().strip()
                    if 'chapter' in text_node:
                        chap_tit_raw = text_node
                        break
                    elif 'episode' in text_node:
                        chap_tit_raw = text_node
                        break
                    elif text_node[0].isdigit():
                        chap_tit_raw = text_node
                        break

        chap_tit_raw = chap_tit_raw.replace('\u203d', '?!').replace('\n', '').replace("\u2018", "'").replace("\u2019", "'").encode("ascii", errors="ignore").decode()
        chap_tit = re.search(r'(\d+\s{0,2}:|\d+\s{0,2}-|\d+)(.*)$', chap_tit_raw.lower())

        if not chap_tit:
            chap_tit = 'untitled'
            chap_tit_id = 0
        elif 'translator' in chap_tit.group(2):
            chap_tit = re.search(r'(.*)(translator(.*))$', chap_tit.group(2))
            chap_tit = chap_tit.group(1).strip()
            chap_tit_id = int(re.findall('\d+', chap_tit_raw)[0])
        else:
            if not chap_tit.group(2).strip():
                chap_tit = 'untitled'
            else:
                chap_tit = chap_tit.group(2).strip()
            chap_tit_id = int(re.findall('\d+', chap_tit_raw)[0])

        chap_content_raw = r_chap.html.find('.reading-content p')
        chap_content_filtered = self.raw_html_text_filter(chap_content_raw)

        b_chap = {
            'c_id': chap_tit_id,
            'c_title': chap_tit,
            'c_content': ''.join(chap_content_filtered),
        }
        return b_chap

    def bn_get_update_book_chaps(self, book, book_url, s_to=0):
        s_to = s_to + 1 if s_to else s_to
        b_chaps_len = book.chapters_count
        c_ids = list(range(b_chaps_len + 1, s_to)) if s_to else False

        if s_to:
            for c_id in c_ids:
                bn_chap_url = f'{book_url}/chapter-{c_id}'
                b_chap = self.bn_get_book_chap(bn_chap_url)
                if b_chap['c_title'] and b_chap['c_content']:
                    self.create_book_chapter(book, b_chap['c_title'], b_chap['c_content'])
                else:
                    break
            b_chap_info = {
                'updated': len(c_ids),
                'last': f'{book_url}/chapter-{c_ids[-1]}',
            }
            return b_chap_info
        else:
            b_chaps_upd = 0
            while True:
                b_chaps_len += 1
                b_chaps_upd += 1
                bn_chap_url = f'{book_url}/chapter-{b_chaps_len}'
                try:
                    b_chap = self.bn_get_book_chap(bn_chap_url)
                    if b_chap['c_title'] and b_chap['c_content']:
                        self.create_book_chapter(book, b_chap['c_title'], b_chap['c_content'])
                    else:
                        raise IndexError
                except IndexError as e:
                    try:
                        b_chaps_len += 1
                        bn_chap_url = f'{book_url}/chapter-{b_chaps_len}'
                        b_chap = self.bn_get_book_chap(bn_chap_url)
                        if b_chap['c_title'] and b_chap['c_content']:
                            self.create_book_chapter(book, 'blank', '')
                            self.create_book_chapter(book, b_chap['c_title'], b_chap['c_content'])
                        else:
                            raise IndexError
                    except IndexError as e:
                        b_chap_info = {
                            'updated': b_chaps_upd,
                            'last': bn_chap_url,
                        }
                        break
            return b_chap_info

    def gt_get_book_cids(self, book_url, s_from=0, s_to=0):
        driver = webdriver.Chrome(chrome_options=self.driver_opts)
        wait = WebDriverWait(driver, 5)
        driver.get(book_url)
        # DOM
        if s_to:
            c_list = wait.until(lambda driver: driver.find_elements_by_css_selector('#chapters .tab-content a')[s_from:s_to])
        else:
            c_list = wait.until(lambda driver: driver.find_elements_by_css_selector('#chapters .tab-content a'))
        c_ids = [a.get_attribute("href") for a in c_list]
        driver.close()
        return c_ids

    def gt_get_book_chap(self, chap_url):
        session = HTMLSession()
        r_chap = session.get(chap_url)
        chap_tit_raw = ''

        h3_tit = r_chap.html.find('#chapterContent h3')
        nodes = r_chap.html.find('#chapterContent p')[:5]
        if not nodes:
            nodes = r_chap.html.find('#chapterContent')[0].text.split('\n')[:8]

        if h3_tit:
            h3_0 = h3_tit[0].text.lower()
            if 'chapter' in h3_0 or 'episode' in h3_0:
                chap_tit_raw = h3_0
        elif len(nodes) >= 4:
            for node in nodes:
                if isinstance(node, str):
                    text_node = node.lower().strip()
                else:
                    if '<strong>' in node.html and 'chapter' in node.text.lower():
                        try:
                            text_node = multiple_replace(
                                self.to_repl,
                                re.search('<strong>(.*)</strong>', node.html)[1]
                            ).replace('<br/>', '').lower().strip()
                        except TypeError:
                            text_node = node.text
                    else:
                        text_node = node.text.lower().strip()
                if 'chapter' in text_node and 'sponsored' not in text_node:
                    chap_tit_raw = text_node
                    if 'sponsored by' in chap_tit_raw:
                        chap_tit_raw = 'untitled'
                    break
                elif 'episode' in text_node:
                    chap_tit_raw = text_node
                    break
                # elif 'preview:' in text_node or 'teaser' in text_node:
                #     return False
                elif text_node[:1].isdigit():
                    chap_tit_raw = text_node
        elif len(nodes) == 1 and '<br/>' in nodes[0].html:
            html_nodes = nodes[0].html.split('<br/>')[:5]
            for node in html_nodes:
                if 'chapter' in node.lower():
                    chap_tit_raw = multiple_replace(self.to_repl, node)
        else:
            if 'chapter' in nodes[0].text.lower():
                chap_tit_raw = nodes[0].text.lower()

        if 'shuras-wrath' in chap_url:
            for node in nodes[:5]:
                if '<strong>' in node.html:
                    if 'chapter' in node.text.lower():
                        chap_tit_raw = node.text.lower().strip()
                    else:
                        chap_tit_raw = f'chapter 0: {node.text}'
                    break

        if 'zhan-long' in chap_url:
            for node in nodes[:5]:
                if 'chapter' in node.text.lower() and '<br/>' in node.html:
                    brs = node.html.split('<br/>')
                    chap_tit_raw = multiple_replace(self.to_repl, brs[0])

        chap_tit_raw = chap_tit_raw.replace('\u203d', '?!').replace('\n', '').replace("\u2018", "'").replace("\u2019", "'").encode("ascii", errors="ignore").decode()
        chap_tit = re.search(r'(\d+\s{0,2}:|\d+\s{0,2}-|\d+)(.*)$', chap_tit_raw.lower())

        if not chap_tit or len(chap_tit.group(2)) >= 150:
            chap_tit = 'untitled'
            chap_tit_id = 0
        elif 'translator' in chap_tit.group(2):
            chap_tit = re.search(r'(.*)(translator(.*))$', chap_tit.group(2))
            chap_tit = chap_tit.group(1).strip()
            chap_tit_id = int(re.findall('\d+', chap_tit_raw)[0])
        else:
            if not chap_tit.group(2).strip():
                chap_tit = 'untitled'
            else:
                chap_tit = chap_tit.group(2).strip()
            chap_tit_id = int(re.findall('\d+', chap_tit_raw)[0])

        chap_content_raw = r_chap.html.find('#chapterContent p')
        if not chap_content_raw:
            chap_content_raw = r_chap.html.find('#chapterContent')[0].text.split('\n')
        elif len(chap_content_raw) == 1 and '<br/>' in chap_content_raw[0].html:
            chap_content_raw = chap_content_raw[0].html.split('<br/>')
        chap_content_filtered = self.raw_html_text_filter(chap_content_raw)

        if 'shuras-wrath' in chap_url:
            if chap_tit.lower() in chap_content_filtered[0].lower():
                del chap_content_filtered[0]
        if 'the-new-world' in chap_url:
            chap_content_filtered = self.raw_html_filter(r_chap.html.find('#chapterContent')[0].html)

        b_chap = {
            'c_id': chap_tit_id,
            'c_title': chap_tit,
            'c_content': ''.join(chap_content_filtered),
        }
        return b_chap

    def gt_get_update_book_chaps(self, book, book_url, c_ids):
        b_chap_url = ''
        b_chap = ''
        for c_url in c_ids[book.chapters_count:]:
            b_chap_url = c_url
            b_chap = self.gt_get_book_chap(b_chap_url)
            if isinstance(b_chap, dict):
                self.create_book_chapter(book, b_chap['c_title'], b_chap['c_content'])
            else:
                break
        b_chap = b_chap['c_title'] if isinstance(b_chap, dict) else b_chap
        b_chap_info = {
            'Source': 'gravity tails',
            'locked_ended_from': b_chap,
            'locked_ended_from_url': b_chap_url,
        }
        return b_chap_info
