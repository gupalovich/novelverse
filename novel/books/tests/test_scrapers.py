from django.test import Client, TestCase, tag
# from unittest import skip

from ..scrapers import BookScraper


class BookScraperTest(TestCase):
    def setUp(self):
        self.scraper = BookScraper()
        self.client = Client()
        self.wn_book_ids = ['20134751006091605', '14187175405584205', '19100202406400905']
        self.wn_chap_ids = ['54201840178355633', '54048846463951458', '54827256119359229']
        self.pd_book_ids = [
            'blood-warlock-succubus-partner-in-the-apocalypse(IN)-1122',
            'birth-of-the-demonic-sword(IN)-74']

    @tag('slow')  # +3s
    def test_webnovel_get_book_data(self):
        for book_id in self.wn_book_ids:
            url = self.scraper.urls['webnovel'] + book_id
            data = self.scraper.webnovel_get_book_data(url)
            self.assertTrue(len(data) == 7)
            self.assertTrue(len(data['book_title']))
            self.assertTrue(len(data['book_description']) >= 100)
            self.assertTrue('img' in data['book_poster_url'])

    @tag('slow')  # + 8s
    def test_webnovel_get_book_volumes(self):
        url = self.scraper.urls['webnovel'] + self.wn_book_ids[0]
        data = self.scraper.webnovel_get_book_volumes(url)
        self.assertTrue(len(data) >= 2)
        for i in data:
            self.assertTrue(isinstance(i, int))

    @tag('slow')  # + 20s
    def test_webnovel_get_chap_ids(self):
        """Test get chapter ids from 3 books"""
        for i, book_id in enumerate(self.wn_book_ids):
            url = self.scraper.urls['webnovel'] + book_id
            if i == 0:
                data = self.scraper.webnovel_get_chap_ids(url)
                self.assertTrue(len(data) >= 500)
            else:
                data = self.scraper.webnovel_get_chap_ids(url, s_from=2, s_to=12)
                self.assertTrue(len(data) == 10)

    @tag('slow')  # + 20s
    def test_webnovel_get_chap(self):
        """Test 3 chapter types: info-0, normal-1, locked-2"""
        for i, chap_id in enumerate(self.wn_chap_ids):
            url = f'{self.scraper.urls["webnovel"]}{self.wn_book_ids[0]}/{chap_id}'
            data = self.scraper.webnovel_get_chap(url)
            self.assertTrue(isinstance(data, dict))
            if i == 2:
                self.assertFalse(len(data))
                continue
            elif i == 1:
                self.assertTrue(len(data) == 5)
                self.assertTrue(data['c_id'] == 1)
                self.assertTrue(len(data['c_thoughts']) >= 200)
            elif i == 0:
                self.assertTrue(len(data) == 5)
                self.assertTrue(data['c_id'] == 'info')
            self.assertTrue(len(data['c_title']) >= 5)
            self.assertTrue(len(data['c_content']) >= 200)
            self.assertTrue(isinstance(data['c_comments'], list))
            self.assertTrue(len(data['c_comments']) >= 5)

    @tag('slow')  # + 10s
    def test_panda_get_chap_ids(self):
        chap_names = [
            'https://www.panda-novel.com/content/blood-warlock-succubus-partner-in-the-apocalypse(IN)-1122-798371/chapter-1--soul-records',
            'https://www.panda-novel.com/content/birth-of-the-demonic-sword(IN)-74-76726/chapter-1--01-birth']
        for i, book_id in enumerate(self.pd_book_ids):
            url = self.scraper.urls['pandanovel'] + 'details/' + book_id
            data = self.scraper.panda_get_chap_ids(url)
            self.assertTrue(len(data) >= 10)
            self.assertTrue(chap_names[i] in data)
