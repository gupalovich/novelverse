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
        self.driver_opts.add_argument('headless')
        self.driver_opts.add_argument('disable-gpu')
        self.driver_opts.add_argument('log-level=3')
        self.driver_opts.add_argument('lang=en-US')
        self.driver_opts.add_argument('silent')

    def setup_user_agent(self):
        user_agent = UserAgent()
        user_agent = user_agent.random
        self.driver_opts.add_argument(f'user-agent={user_agent}')

    def sel_find_css(self, driver, selector, many=False):
        """Selenium find_element/s shortcut"""
        if many:
            return driver.find_elements(by=By.CSS_SELECTOR, value=selector)
        else:
            return driver.find_element(by=By.CSS_SELECTOR, value=selector)

    def sel_wait_until(self, driver, selector, delay=5):
        """Selenium wait.until shortcut"""
        wait = WebDriverWait(driver, delay)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))

    def webnovel_get_book_data(self, book_url: str) -> dict:
        """GET webnovel book data with html_requests
           TODO: chap_release_raw = r.html.find('.det-hd-detail strong')[0].text
                 chap_release = chap_release_raw.lower().strip() if len(chap_release_raw) < 20 else int(re.findall('\d+', chap_release_raw)[0])"""
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
                'c_origin': 'webnovel',
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

    def panda_get_chap(self, chap_url: str) -> dict:
        chap_data = {}
        driver = webdriver.Chrome(options=self.driver_opts)
        driver.get(chap_url)
        self.sel_wait_until(driver, '.novel-content')
        chap_title_raw = self.sel_find_css(driver, '.novel-content h2').text
        try:
            chap_title = re.split(
                r':|-|–', chap_title_raw, maxsplit=1)[1]
        except IndexError:
            """TODO: str w/o number will break normal order"""
            chap_title = re.split(r'\s+', chap_title_raw, maxsplit=1)[1]
        chap_title = chap_title.strip().replace('‽', '?!')
        chap_id = int(re.findall(r'\d+', chap_title_raw)[0])
        chap_next = self.sel_find_css(driver, 'a.btn-next').get_attribute('href')
        chap_content_raw = self.sel_find_css(driver, '.novel-content div', many=True)
        chap_content = ''
        for p_raw in chap_content_raw:
            parags = p_raw.text.split('\n')
            if not parags:
                continue
            for pg in parags:
                pg = pg.strip()
                pg_letters = re.sub(r'[^a-zA-Z]+', '', pg.lower())
                if not pg:
                    continue
                if re.search(r"\[.*?\]", pg) or re.search(r"\*.*?\*", pg):  # between [ ] or * *
                    chap_content += f'<p><b>{pg}</b></p>'
                elif 'pandanovel' in pg_letters:
                    with open('chap_watermarks.txt', 'a', encoding='utf-8') as f:
                        f.write(pg + '\n')
                else:
                    chap_content += f'<p>{pg}</p>'
        chap_data.update({
            'c_id': chap_id,
            'c_title': chap_title,
            'c_content': chap_content,
            'c_next': chap_next,
            'c_origin': 'pandanovel',
        })
        return chap_data

    def run(self):
        from pprint import pprint
        url = 'https://www.panda-novel.com/content/the-oracle-paths(JN)-162-165078/chapter-1-the-day-everything-changed'
        while True:
            try:
                data = self.panda_get_chap(url)
                url = data['c_next']
                print(data['c_id'], data['c_title'])
                if not url:
                    print('Stopped at:', data['c_id'])
                    break
            except Exception as e:
                print(e)


if __name__ == '__main__':
    logging.basicConfig(level=logging.WARNING, format='%(name)-24s: %(levelname)-8s %(message)s')
    start = datetime.now()

    scraper = BookScraper()
    scraper.run()

    finish = datetime.now() - start
    logging.info(f'Done in: {finish}')


class BookScraper2:
    def __init__(self):
        self.driver_opts = webdriver.ChromeOptions()
        self.driver_opts.add_argument('headless')
        self.driver_opts.add_argument('disable-gpu')
        self.driver_opts.add_argument('log-level=3')
        self.driver_opts.add_argument('silent')

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
