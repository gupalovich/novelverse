import factory
from celery import states
from django.test import TestCase, tag
from django.db.models import signals

from ..models import Book, BookGenre, BookChapter
from ..scrapers import BookScraper
from ..tasks import (
    update_bookchapter_title_slug,
    update_book_ranking,
    update_book_revisited,
    book_scraper_info,
    book_scraper_chaps,
    book_revisit_novel,
)


class BookTasksTest(TestCase):
    @factory.django.mute_signals(signals.post_save)
    def setUp(self):
        self.scraper = BookScraper()
        self.bookgenre = BookGenre.objects.create(name='test genre')
        self.book = Book.objects.create(title='test book one', bookgenre=self.bookgenre, votes=134, status=1, visit_id='6831850602000905')
        self.book_1 = Book.objects.create(title='test book two', bookgenre=self.bookgenre, votes=34, status=1, visit_id='7931338406001705')
        self.book_2 = Book.objects.create(title='test book three', bookgenre=self.bookgenre, votes=74, status=1, visit_id='7176992105000305')
        self.book_3 = Book.objects.create(
            title='Age of Adepts', bookgenre=self.bookgenre, status=1,
            visit='gravitytails', visit_id='age-of-adepts',
            revisit='gravitytails', revisit_id='age-of-adepts',
            visited=True,
        )
        self.long_title = 'long title' * 25
        self.b_chap = BookChapter.objects.create(book=self.book, title=self.long_title)
        self.b_chap_1 = BookChapter.objects.create(book=self.book, title=self.long_title)

    def test_update_bookchapter_title_slug(self):
        self.b_chap_1.title = 'test title'
        self.b_chap_1.save()
        res = update_bookchapter_title_slug.apply()
        self.book.refresh_from_db()
        self.b_chap.refresh_from_db()
        self.b_chap_1.refresh_from_db()
        self.assertEqual(res.state, states.SUCCESS)
        self.assertEqual(self.b_chap.title.lower(), 'untitled')
        self.assertEqual(self.b_chap_1.title.lower(), 'test title')

    def test_update_book_ranking(self):
        self.assertEqual(self.book.ranking, 0)
        self.assertEqual(self.book_1.ranking, 0)
        self.assertEqual(self.book_2.ranking, 0)
        res = update_book_ranking.apply()
        self.book.refresh_from_db()
        self.book_1.refresh_from_db()
        self.book_2.refresh_from_db()
        self.assertEqual(res.state, states.SUCCESS)
        self.assertEqual(self.book.ranking, 1)
        self.assertEqual(self.book_1.ranking, 3)
        self.assertEqual(self.book_2.ranking, 2)

    @factory.django.mute_signals(signals.post_save)
    def test_update_book_revisited(self):
        self.book.revisited = True
        self.book.save()
        self.book_1.revisited = True
        self.book_1.save()
        self.book.refresh_from_db()
        self.book_1.refresh_from_db()
        self.assertTrue(self.book.revisited)
        self.assertTrue(self.book_1.revisited)
        res = update_book_revisited.delay()
        self.book.refresh_from_db()
        self.book_1.refresh_from_db()
        self.assertEqual(res.state, states.SUCCESS)
        self.assertFalse(self.book.revisited)
        self.assertFalse(self.book_1.revisited)

    @tag('slow')  # 30s
    def test_book_scraper_initial_webnovel(self):
        """
        Test celery initial scraper info + unlocked chapters
        s_to=5 (first 5 chapters)
        """
        s_to = 5
        res = book_scraper_info.apply_async(args=(self.book.pk, ))
        self.book.refresh_from_db()
        book_tags = self.book.booktag.all()
        c_count = self.book.bookchapters.count()
        self.assertEqual(res.state, states.SUCCESS)
        self.assertEqual(self.book.title, "Library Of Heaven's Path")
        self.assertIn('Cultivation', [b_tag.name for b_tag in book_tags])
        self.assertIn('Weak To Strong', [b_tag.name for b_tag in book_tags])
        self.assertEqual(c_count, 0)
        self.assertTrue(self.book.visited)

        res = book_scraper_info.apply_async(args=(self.book.pk, ))
        self.assertEqual(res.state, states.IGNORED)

        res = book_scraper_chaps.apply_async(args=(self.book.pk, ), kwargs={'s_to': s_to, })
        self.book.refresh_from_db()
        b_chaps = self.book.bookchapters.all()
        b_chaps_list = list(b_chaps)
        b_chaps_l = b_chaps_list[0]
        b_chaps_f = b_chaps_list[-1]
        self.assertEqual(res.state, states.SUCCESS)
        self.assertEqual(len(b_chaps_list), s_to)
        self.assertEqual(b_chaps_f.slug, 'swindler')
        self.assertEqual(b_chaps_l.slug, 'young-mistress')

    @tag('slow')  # 30s
    def test_book_scraper_initial_gravitytails(self):
        """
        Test celery initial scraper info + unlocked chapters
        s_to=5 (first 5 chapters)
        """
        s_to = 5
        res = book_scraper_chaps.apply_async(args=(self.book_3.pk, ), kwargs={'s_to': s_to, })
        self.book.refresh_from_db()
        b_chaps = self.book_3.bookchapters.all()
        print(b_chaps)
        b_chaps_list = list(b_chaps)
        b_chaps_l = b_chaps_list[0]
        b_chaps_f = b_chaps_list[-1]
        self.assertEqual(res.state, states.SUCCESS)
        self.assertEqual(len(b_chaps_list), s_to)
        self.assertEqual(b_chaps_f.slug, 'prologue')
        self.assertEqual(b_chaps_l.slug, 'garden-of-whispers')
        self.assertTrue(len(b_chaps_f.text) > 100)
        self.assertTrue(len(b_chaps_l.text) > 100)

    @tag('slow')  # 30s
    def test_book_scraper_revisit_webnovel(self):
        s_to = 4
        self.book.visited = True
        self.book.revisit_id = self.book.visit_id
        self.book.save()
        self.book.refresh_from_db()
        BookChapter.objects.create(book=self.book, title='test 1')
        BookChapter.objects.create(book=self.book, title='test 2')
        b_chaps = self.book.bookchapters.all()
        b_chaps_list = list(b_chaps)
        b_chaps_f = b_chaps_list[0]
        b_chaps_l = b_chaps_list[-1]
        self.assertEqual(b_chaps_f.slug, 'test-2')
        self.assertEqual(b_chaps_l.slug, 'test-1')

        res = book_revisit_novel.apply_async(args=[self.book.pk], kwargs={'s_to': s_to, })
        self.book.refresh_from_db()
        b_chaps = list(self.book.bookchapters.all())
        self.assertFalse(self.book.revisited)
        self.assertEqual(res.state, states.SUCCESS)
        self.assertEqual(self.book.bookchapters.count(), s_to)
        self.assertEqual(b_chaps[1].slug, 'imperfections-in-heavens-path')
        self.assertEqual(b_chaps[0].slug, 'slapping-face')
        self.assertTrue(len(b_chaps[1].text) > 3000)
        self.assertTrue(len(b_chaps[0].text) > 3000)

    @tag('slow')  # 30s
    def test_book_scraper_revisit_boxnovel(self):
        s_to = 4
        self.book.visited = True
        self.book.revisit = 'boxnovel'
        self.book.revisit_id = 'library-of-heavens-path'
        self.book.save()
        self.book.refresh_from_db()
        BookChapter.objects.create(book=self.book, title='test 1')
        BookChapter.objects.create(book=self.book, title='test 2')
        b_chaps = self.book.bookchapters.all()
        b_chaps_list = list(b_chaps)
        b_chaps_f = b_chaps_list[0]
        b_chaps_l = b_chaps_list[-1]
        self.assertEqual(b_chaps_f.slug, 'test-2')
        self.assertEqual(b_chaps_l.slug, 'test-1')

        # boxnovel for loop
        res = book_revisit_novel.apply_async(args=[self.book.pk], kwargs={'s_to': s_to, })
        # boxnovel while loop
        # res = book_revisit_novel.apply_async(args=[self.book.pk])
        self.book.refresh_from_db()
        b_chaps = list(self.book.bookchapters.all())
        self.assertFalse(self.book.revisited)
        self.assertEqual(res.state, states.SUCCESS)
        self.assertEqual(self.book.bookchapters.count(), s_to)
        self.assertEqual(b_chaps[1].slug, 'imperfections-in-heavens-path')
        self.assertEqual(b_chaps[0].slug, 'slapping-face')
        self.assertTrue(len(b_chaps[1].text) > 3000)
        self.assertTrue(len(b_chaps[0].text) > 3000)

    @tag('slow')
    def test_boxnovel_chapter_availability(self):
        self.book.chapters_count = 1410
        self.book.visited = True
        self.book.revisit = 'boxnovel'
        self.book.revisit_id = 'my-youth-began-with-him'
        self.book.save()
        self.book.refresh_from_db()
        res = book_revisit_novel.apply_async(args=[self.book.pk], kwargs={'s_to': 1420})
        self.book.refresh_from_db()
        b_chaps = list(self.book.bookchapters.all())

    @tag('slow')
    def test_webnovel_chapter_get_content(self):
        b_chap_url = 'https://www.webnovel.com/book/8094085105004705/21727394347290635'
        b_chap = self.scraper.wn_get_book_chap(b_chap_url)
        # print(b_chap)
        with open("b_chap.txt", "w+") as f:
            f.write(str(b_chap))

    @tag('slow')
    def test_boxnovel_chapter_get_content(self):
        b_chap_url = 'https://boxnovel.com/novel/advent-of-the-archmage/chapter-726-end/'
        b_chap = self.scraper.bn_get_book_chap(b_chap_url)
        # print(b_chap)
        with open("b_chap.txt", "w+") as f:
            f.write(str(b_chap))

    # @tag('slow')
    def test_gravitytails_chapter_get_content(self):
        b_chap_url = 'http://gravitytales.com/novel/shuras-wrath/sw-chapter-850'
        b_chap = self.scraper.gt_get_book_chap(b_chap_url)
        # print(b_chap)
        with open("b_chap.txt", "w+") as f:
            f.write(str(b_chap))
