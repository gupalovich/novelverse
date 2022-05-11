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

from .utils import multiple_replace


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

    def webnovel_get_book_data(self, book_url: str, volumes=True) -> dict:
        """GET webnovel book data with html_requests"""
        session = HTMLSession()
        r = session.get(book_url)
        book = {}
        if len(r.html.find('h1.pt4 small')[0].text):
            b_title_raw = r.html.find('h1.pt4')[0].text
            b_title = ' '.join(b_title_raw.split(' ')[0:-1])
            b_title_sm = r.html.find('h1.pt4 small')[0].text
        else:
            b_title = r.html.find('h1.pt4')[0].text
            b_title_sm = ''
        b_desc_raw = r.html.find('.j_synopsis')[0].text
        b_desc = ''.join([f'<p>{i}</p>' for i in b_desc_raw.split('\n') if i])
        b_tags = [tag.text.replace('# ', '').lower() for tag in r.html.find('p.m-tag')]
        try:
            b_author = r.html.find('h2.ell.dib.vam a')[0].text
        except IndexError:
            try:
                b_author = r.html.find('h2.ell.dib.vam span')[0].text
            except IndexError:
                b_author = ''
        b_rating = float(r.html.find('._score.ell strong')[0].text)
        b_poster_url = r.html.find('i.g_thumb img')[1].attrs['src']
        b_volumes = self.webnovel_get_book_volumes(book_url) if volumes else [1, ]
        book.update({
            'book_title': b_title,
            'book_title_sm': b_title_sm,
            'book_description': b_desc,
            'book_tags': b_tags,
            'book_author': b_author,
            'book_rating': b_rating,
            'book_poster_url': b_poster_url,
            'book_volumes': b_volumes,
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
            chap_title = self.slice_bookchapter_title(chap_title_raw)
            try:
                chap_id = int(re.findall(r'\d+', chap_title_raw)[0])
            except IndexError:
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

    def panda_remove_watermarks(self, text: str) -> str:
        """Search/remove pandanovel watermarks"""
        fillers = [
            'Update faster? please come to',
            'update faster perks? google search',
            'Do you want to read more chapters?',
            'Want to see more chapters?',
            'If you want to read more chapters, visit',
            'Remember to remove punctuation',
            'Please come to', 'Come to', 'Please visit',
            'update faster',
        ]
        patterns = [
            # search patterns 'pandanovelcom'
            r'p[\s]a[\s]n.+c[.,\s]o[.,\s]m',
            r'pan.+c[.,\s]o[.,\s]m',
            r'pa.+c[.,\s]o[.,\s]m',
            r'p[.,]a.+com',
            r'pa.+c[.,]om',
            r'pa.+com',
            # search patterns 'pandanovel'
            r'pa.+el',
            r'pan.+vel',
            r'p[.\-,\s]a.+vel',
            r'pan.+v[.,\s]e[.,\s]l',
            r'pa.+ve[.,\s]l',
        ]
        for filler in sorted(fillers, key=len, reverse=True):
            text = text.replace(filler, '')
        result = None
        for pattern in patterns:
            result = re.search(pattern, text, re.I)
            if result:
                result = text.replace(result.group(), ' ')
                break
        return result

    def panda_get_chap(self, chap_url: str) -> dict:
        """Build/clean pandanovel chapter content"""
        chap_data = {}
        driver = webdriver.Chrome(options=self.driver_opts)
        driver.get(chap_url)
        self.sel_wait_until(driver, '.novel-content')
        chap_title_raw = self.sel_find_css(driver, '.novel-content h2').text
        chap_title = self.slice_bookchapter_title(chap_title_raw).replace('&amp;', '&')
        chap_id = int(re.findall(r'\d+', chap_title_raw)[0])
        chap_next = self.sel_find_css(driver, 'a.btn-next').get_attribute('href')
        chap_content_raw = self.sel_find_css(driver, '.novel-content div', many=True)
        chap_content = ''
        for p_raw in chap_content_raw:
            parags = p_raw.text.replace('â\x80¦', '').split('\n')  # content split in </br>
            if not parags:
                continue
            for pg in parags:
                pg = pg.strip()
                if not pg:
                    continue
                pg_letters = re.sub(r'[^a-zA-Z]+', '', pg.lower())
                if 'pandanovel' in pg_letters:
                    pg = self.panda_remove_watermarks(pg)
                    if not pg:
                        continue
                    pg_letters = re.sub(r'[^a-zA-Z]+', '', pg.lower())  # double check
                    if 'pandanovel' in pg_letters:
                        with open('chap_watermarks.txt', 'a', encoding='utf-8') as f:
                            f.write(pg + '\n')

                if re.search(r"^\[.*?\]$", pg) or re.search(r"^\*.*?\*$", pg):  # between [] **
                    chap_content += f'<p><b>{pg}</b></p>'
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

    def slice_bookchapter_title(self, title):
        patterns = [
            r'chapter.*\d+[:.\s].*\d+[.:]',
            r'chapter.*\d+[:.\s]',
            r'^\d+.*chapter.*\d+',
            r'^\d+[:.\s]',
            r'^\d+.*[-]',
        ]
        for pattern in patterns:
            pattern = re.compile(pattern, re.IGNORECASE)
            match = re.match(pattern, title)
            if match:
                title = re.split(pattern, title, maxsplit=1)
                title = title[1] if len(title) == 2 else title[0]
                break
        if title.startswith('-') or title.startswithfro(':') or title.startswith('.'):
            title = title[1:]
        return title.strip()


if __name__ == '__main__':
    logging.basicConfig(level=logging.WARNING, format='%(name)-24s: %(levelname)-8s %(message)s')
    start = datetime.now()

    scraper = BookScraper()
    scraper.run()

    finish = datetime.now() - start
    logging.info(f'Done in: {finish}')
