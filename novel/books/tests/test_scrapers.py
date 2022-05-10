from django.test import Client, TestCase, tag
# from unittest import skip

from ..scrapers import BookScraper


class BookScraperTest(TestCase):
    def setUp(self):
        self.scraper = BookScraper()
        self.client = Client()
        self.wn_book_ids = ['20134751006091605', '11022733006234505', '19100202406400905']
        self.wn_chap_ids = ['54201840178355633', '54048846463951458', '54827256119359229']
        self.pd_book_ids = [
            'blood-warlock-succubus-partner-in-the-apocalypse(IN)-1122',
            'birth-of-the-demonic-sword(IN)-74']
        self.pd_chap_urls = [
            'https://www.panda-novel.com/content/blood-warlock-succubus-partner-in-the-apocalypse(IN)-1122-798371/chapter-1--soul-records',
            'https://www.panda-novel.com/content/birth-of-the-demonic-sword(IN)-74-76726/chapter-1--01-birth']

    @tag('slow')  # +3-40s
    def test_webnovel_get_book_data(self, volumes=False):  # volumes add 30s+ to test
        for book_id in self.wn_book_ids:
            url = self.scraper.urls['webnovel'] + book_id
            data = self.scraper.webnovel_get_book_data(url, volumes=volumes)
            self.assertTrue(len(data) == 8)
            self.assertTrue(len(data['book_title']))
            self.assertTrue(len(data['book_description']) >= 100)
            self.assertTrue('img' in data['book_poster_url'])
            self.assertTrue(isinstance(data['book_tags'], list))
            self.assertTrue(len(data['book_poster_url']) >= 10)
            self.assertTrue(isinstance(data['book_volumes'], list))
            self.assertTrue(len(data['book_volumes']) >= 1)

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
                self.assertTrue(len(data) == 6)
                self.assertTrue(data['c_id'] == 1)
                self.assertTrue(len(data['c_thoughts']) >= 200)
            elif i == 0:
                self.assertTrue(len(data) == 6)
                self.assertTrue(data['c_id'] == 'info')
            self.assertTrue(len(data['c_title']) >= 5)
            self.assertTrue(len(data['c_content']) >= 200)
            self.assertTrue(isinstance(data['c_comments'], list))
            self.assertTrue(len(data['c_comments']) >= 5)
            self.assertTrue(data['c_origin'] == 'webnovel')

    @tag('slow')  # + 10s
    def test_panda_get_chap_ids(self):
        for i, book_id in enumerate(self.pd_book_ids):
            url = self.scraper.urls['pandanovel'] + 'details/' + book_id
            data = self.scraper.panda_get_chap_ids(url)
            self.assertTrue(len(data) >= 10)

    @tag('slow')  # + 10s
    def test_panda_get_chap(self):
        for url in self.pd_chap_urls:
            data = self.scraper.panda_get_chap(url)
            self.assertTrue(isinstance(data, dict))
            self.assertTrue(len(data) == 5)
            self.assertTrue(isinstance(data['c_id'], int))
            self.assertTrue(len(data['c_title']) >= 4)
            self.assertTrue(len(data['c_content']) >= 500)
            self.assertTrue('panda-novel.com/content' in data['c_next'])

    def test_panda_remove_watermarks(self):
        examples = [
            'Please come to p.a.n.d.a n.ovel',
            'Please come to p a.n.d.a n.ovel',
            'Please come to p,a.n.d.a n.ovel.com',
            'Please come to p-a.n.d.a n.ovel',
            'Update faster? please come to P.an.da N.o.vel',
            'Update faster? please come to P.an.da No.vel',
            'Update faster? please come to Pan.da N.o.vel',
            'Update faster? please come to panda-novel.c.om',
            'update faster perks? google search pan.da no.ve.l',
            'update faster perks? google search pan.da no.vel',
            'Do you want to read more chapters? Come to panda-novel,com',
            'Come to panda-novel,com',
            'Panda Novel',
            'Please visit panda-novel ,com',
            'Please visit panda-novel ,com',
            'Please visit panda-novel ,c.o.m',
            'Want to see more chapters? Please visit pan da-novel ,c.o.m',
            'If you want to read more chapters, visit pa nda-novel,c.o,m',
            'Want to see more chapters? Please visit p a n d a -n o v e l .c o m',
            'Do you want to read more chapters? Come to p a n d a - n ovel,c.o.m',
            'Do you want to read more chapters? Come to p a n d a - n o v e l,c.o.m',
            'Want to see more chapters? Please visit p a n d a -n o v e l .c o m',
            'Please visit p a n d a - n o v e l ,c o m',
        ]
        for i, text in enumerate(examples):
            result = self.scraper.panda_remove_watermarks(text)
            if result:
                examples[i] = result
        for example in examples:
            self.assertTrue(len(example) <= 5)

    def test_slice_bookchapter_title(self):
        examples = [
            'Chapter 1: Testing the Dragon Form',
            'Chapter 29: 29. Testing the Dragon Form',
            'Chapter 842: Chapter 836: Testing the Dragon Form',
            'Chapter 41 Testing the Dragon Form',
            'Chapter 736 - Testing the Dragon Form',
            'Chapter 736 : Testing the Dragon Form',
            '736 - Testing the Dragon Form',
            '7: Testing the Dragon Form',
            '736. Testing the Dragon Form',
            '736 Testing the Dragon Form',
            'Testing the Dragon Form',
        ]
        for i, example in enumerate(examples):
            examples[i] = self.scraper.slice_bookchapter_title(example)
            self.assertTrue(examples[i] == 'Testing the Dragon Form')
