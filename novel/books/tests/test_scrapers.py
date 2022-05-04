import factory
from django.test import Client, TestCase, tag
from django.db.models import signals
from unittest import skip

from ..models import Book, BookGenre, BookTag
from ..utils import capitalize_str
from ..scrapers import BookScraper


class BookScraperTest(TestCase):
    def setUp(self):
        self.scraper = BookScraper()
        self.client = Client()
        self.wn_book_ids = ['20134751006091605', '14187175405584205', '19100202406400905']
        self.wn_chap_ids = ['54048846463951458', '54201840178355633', '54827256119359229']

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
        print(data)
        self.assertTrue(len(data) >= 2)
        for i in data:
            self.assertTrue(isinstance(i, int))

    @tag('slow')  # + 20s
    def test_webnovel_get_chap_ids(self):
        for i, book_id in enumerate(self.wn_book_ids):
            url = self.scraper.urls['webnovel'] + book_id
            if i == 0:
                data = self.scraper.webnovel_get_chap_ids(url)
                self.assertTrue(len(data) >= 500)
            else:
                data = self.scraper.webnovel_get_chap_ids(url, s_from=2, s_to=12)
                self.assertTrue(len(data) == 10)

    def test_webnovel_get_chap(self):
        pass


@skip('Ignore')
class BookScraperTest2(TestCase):
    @factory.django.mute_signals(signals.post_save)
    def setUp(self):
        self.client = Client()
        self.scraper = BookScraper()
        self.bookgenre = BookGenre.objects.create(name='test genre')
        self.booktag = BookTag.objects.create(name='test')
        self.booktag_1 = BookTag.objects.create(name='tag')
        self.book = Book.objects.create(title='test book', bookgenre=self.bookgenre, status=0,
            visit_id='11530348105422805', revisit_id='my-house-of-horrors'
        )
        self.book_1 = Book.objects.create(title='test book 123', bookgenre=self.bookgenre, status=0, visited=True)
        self.book_2 = Book.objects.create(title='Age of Adepts', bookgenre=self.bookgenre, status=0, visit='gravitytails', revisit='gravitytails',
            visit_id='age-of-adepts', revisit_id='age-of-adepts'
        )
        self.book.booktag.add(self.booktag, self.booktag_1)
        self.tags = ['test', 'tag', 'alo']
        self.chaps = [
            {'title': 'test', 'content': 'test'},
            {'title': 'test1', 'content': 'test'},
            {'title': 'test2', 'content': 'test'}
        ]
        self.wn_url = f'https://www.webnovel.com/book/{self.book.visit_id}/'
        self.wn_url_1 = 'https://www.webnovel.com/book/8360425206000005/'
        self.wn_cids = ['31433161158217963', '31434466845054269', '31435296830706024', '31456481220024926', '31457257803799212', '31458260947098371', '31478999733560367', '31479978986103973', '31481323864516947', '31502076592844451']
        self.wn_cids_1 = ['22941159621980243']
        self.bn_url = f'https://boxnovel.com/novel/{self.book.revisit_id}/'

    def test_get_filter_db_books(self):
        qs = Book.objects.all()
        books = self.scraper.get_filter_db_books(qs)
        self.assertIn(self.book, books)
        self.assertNotIn(self.book_1, books)
        self.book.visited = True
        self.book.save()
        books_revisit = self.scraper.get_filter_db_books(qs, revisit=True)
        self.assertIn(self.book, books_revisit)
        self.assertNotIn(self.book_1, books_revisit)

    def test_create_book_tag(self):
        tag_0 = self.scraper.create_book_tag(self.tags[0])
        tag_1 = self.scraper.create_book_tag(self.tags[1])
        tag_2 = self.scraper.create_book_tag(self.tags[2])
        self.assertFalse(tag_0)
        self.assertFalse(tag_1)
        self.assertEqual(capitalize_str(self.tags[2]), tag_2.name)

    def test_add_book_booktag(self):
        tag_2 = self.scraper.create_book_tag(self.tags[2])  # alo tag
        added = self.scraper.add_book_booktag(self.book, tag_2)
        booktags = self.book.booktag.all()
        books = tag_2.books.all()
        self.assertEqual(capitalize_str(self.tags[2]), tag_2.name)
        self.assertTrue(added)
        self.assertIn(tag_2, booktags)
        self.assertIn(self.book, books)
        self.assertEqual(booktags.count(), 3)
        added = self.scraper.add_book_booktag(self.book, tag_2)
        self.assertFalse(added)

    @tag('slow')  # +12s
    def test_update_db_book_data(self):
        b_data = self.scraper.wn_get_book_data(self.wn_url)[0]
        b_tags = self.book.booktag.all()
        self.scraper.update_db_book_data(self.book, b_data)
        self.assertEqual(self.book.title, b_data['book_name'])
        self.assertEqual(self.book.title_sm, b_data['book_name_sm'])
        self.assertIn(b_data['book_info_author'], self.book.author)
        self.assertEqual(self.book.description, b_data['book_desc'])
        self.assertEqual(self.book.rating, b_data['book_rating'])
        if b_data['chap_release'] == 'completed':
            self.assertEqual(self.book.status, 1)
        elif isinstance(b_data['chap_release'], int):
            self.assertEqual(self.book.status, 0)
            self.assertEqual(self.book.chapters_release, b_data['chap_release'])
        for b_tag in b_data['book_tag_list']:
            self.scraper.create_book_tag(b_tag)
            self.scraper.add_book_booktag(self.book, b_tag)
            self.assertIn(capitalize_str(b_tag), [tag.name for tag in b_tags])

    @factory.django.mute_signals(signals.post_save)
    def test_create_book_chapter(self):
        for chap in self.chaps:
            self.scraper.create_book_chapter(
                self.book, chap['title'], chap['content'])
        bookchapters = self.book.bookchapters.all()
        self.assertEqual(bookchapters.count(), 3)
        self.assertEqual(bookchapters[1].title, capitalize_str(self.chaps[1]['title']))

    @tag('slow')  # +12s
    def test_wn_get_book_data(self):
        resp = self.scraper.wn_get_book_data(self.wn_url)[0]
        self.assertTrue(isinstance(resp['book_desc'], str))
        self.assertTrue(isinstance(resp['book_name'], str))
        self.assertTrue(isinstance(resp['book_name_sm'], str))
        self.assertTrue(isinstance(resp['chap_release'], int))
        self.assertTrue(isinstance(resp['book_info_chap_count'], int))
        self.assertTrue(isinstance(resp['book_info_author'], str))
        self.assertTrue(isinstance(resp['book_rating'], float))
        self.assertTrue(isinstance(resp['book_poster_url'], str))
        self.assertTrue(isinstance(resp['book_tag_list'], list))
        self.assertIn('<p>', resp['book_desc'])
        self.assertNotEqual(len(resp['book_name']), 0)
        self.assertNotEqual(len(resp['book_name_sm']), 0)
        self.assertNotEqual(resp['book_info_chap_count'], 0)
        self.assertNotEqual(len(resp['book_info_author']), 0)
        self.assertNotEqual(len(resp['book_poster_url']), 0)
        self.assertNotEqual(len(resp['book_tag_list']), 0)

    @tag('slow')  # +10s
    def test_wn_book_get_cids(self):
        resp = self.scraper.wn_get_book_cids(self.wn_url, s_to=5)
        self.assertEqual(len(resp), 5)
        self.assertEqual(resp[0], '30952845050180675')

    @tag('slow')  # +4s
    def test_wn_get_book_chap(self):
        url = f'{self.wn_url}{self.wn_cids[0]}'
        url_locked = f'{self.wn_url}{self.wn_cids[5]}'
        resp = self.scraper.wn_get_book_chap(url)
        resp_locked = self.scraper.wn_get_book_chap(url_locked)
        print(resp_locked)
        self.assertTrue(isinstance(resp, dict))
        self.assertTrue(isinstance(resp['c_id'], int))
        self.assertEqual(resp['c_id'], 96)
        self.assertTrue(isinstance(resp['c_title'], str))
        self.assertTrue(isinstance(resp['c_content'], str))
        self.assertIn('<p>', resp['c_content'])
        self.assertTrue(isinstance(resp_locked, str))
        self.assertIn('101', resp_locked.lower())
        self.assertIn('chapter', resp_locked.lower())

    @factory.django.mute_signals(signals.post_save)
    @tag('slow')  # +20s
    def test_wn_get_update_book_chaps(self):
        c_ids = self.scraper.wn_get_book_cids(self.wn_url)
        res = self.scraper.wn_get_update_book_chaps(self.book, self.wn_url, c_ids)
        b_chaps = list(self.book.bookchapters.all())
        self.assertTrue(isinstance(res, dict))
        self.assertEqual(len(b_chaps), 5)
        self.assertEqual(b_chaps[-1].slug, 'dying-house-of-horrors')
        self.assertEqual(b_chaps[0].slug, '25-minutes-and-14-seconds')

    def test_bn_get_book_chap(self):
        pass

    @tag('slow')  # +30s
    def test_bn_get_update_book_chaps(self):
        resp = self.scraper.bn_get_update_book_chaps(self.book, self.bn_url, s_to=5)
        resp_info = resp[-1]
        # test chap content
        for chap in resp[0:-1]:
            self.assertTrue(isinstance(chap['c_id'], int))
            self.assertTrue(isinstance(chap['c_title'], str))
            self.assertNotEqual(chap['c_id'], 0)
            self.assertNotEqual(chap['c_title'], 0)
            self.assertIn('<p>', chap['c_content'])
            self.assertNotIn('<p></p>', chap['c_content'])
            self.assertNotIn('<script>', chap['c_content'])
            self.assertNotIn('<?php', chap['c_content'])
        # test chap resp result
        self.assertTrue(isinstance(resp_info['updated'], int))
        self.assertTrue(isinstance(resp_info['last'], str))
        self.assertNotEqual(resp_info['updated'], 0)
        self.assertNotEqual(len(resp_info['last']), 0)

    @tag('slow')  # +15s
    def test_gt_get_book_cids(self):
        book_url = f'{self.scraper.url_bb["gravitytails"]}{self.book_2.visit_id}'
        s_to = 5
        res = self.scraper.gt_get_book_cids(book_url, s_to=s_to)
        self.assertEqual(len(res), 5)
        self.assertEqual(res[0], 'http://gravitytales.com/novel/age-of-adepts/aoa-chapter-0')
        self.assertEqual(res[-1], 'http://gravitytales.com/novel/age-of-adepts/aoa-chapter-4')
