import factory
import re

from django.test import TestCase
from django.db.models import signals

from ..models import Book, BookTag, BookGenre, BookChapter
from ..utils import (
    capitalize_str,
    capitalize_slug,
    multiple_replace,
    spoon_feed,
    filter_books_visit,
    create_book_tag,
    create_book_chapter,
    add_book_booktag,
    update_book_data,
)


class UtilsTest(TestCase):
    @factory.django.mute_signals(signals.post_save)
    def setUp(self):
        self.slug = 'test-slug-123'
        self.string = 'test string 123'
        self.to_repl = {'<p>': '', '</p>': '', '  ': '', '\n': ''}
        self.text = "'<p>\n</p>\n\n\n    \n     sweat.\n\n\n    \n    \n</p>"
        self.bookgenre = BookGenre.objects.create(name='test genre')
        for i in range(24):
            Book.objects.create(
                title=f'test {i}', bookgenre=self.bookgenre,
                revisited=False,
                visited=False, visit_id='123')
        for i in range(26):
            Book.objects.create(
                title=f'test {i}-', bookgenre=self.bookgenre,
                visited=True,
                revisit_id='123', revisited=False)
        self.books = Book.objects.all()

    def test_capitalize_slug(self):
        self.assertEqual('Test Slug', capitalize_slug(self.slug))

    def test_capitalize_string(self):
        self.assertEqual('Test String 123', capitalize_str(self.string))

    def test_multiple_replace(self):
        text = multiple_replace(self.to_repl, self.text)
        self.assertNotIn('<p>', text)
        self.assertNotIn('</p>', text)
        self.assertNotIn('\n', text)
        self.assertNotIn('  ', text)

    def update_book_title(self, obj):
        obj.title = 'changed'
        obj.save()
        return obj

    def test_spoon_feed(self):
        [i for i in spoon_feed(self.books, self.update_book_title, chunk=10)]
        self.assertEqual('Changed', Book.objects.first().title)
        self.assertEqual('Changed', Book.objects.last().title)

    def test_filter_books_visit(self):
        self.assertTrue(len(self.books) == 50)
        qs_visit = filter_books_visit(self.books)
        qs_revisit = filter_books_visit(self.books, revisit=True)
        self.assertTrue(len(qs_visit) == 24)
        self.assertTrue(len(qs_revisit) == 26)

    def test_create_book_tag(self):
        tag_name = 'Test tag 1'
        book_tags = BookTag.objects.all()
        self.assertFalse(book_tags)
        for i in range(5):
            create_book_tag(tag_name)
        book_tags = BookTag.objects.all()
        self.assertTrue(len(book_tags) == 1)
        self.assertTrue(book_tags[0].name == 'Test Tag 1')
        self.assertTrue(book_tags[0].slug == 'test-tag-1')

    def test_create_book_chapter(self):
        book = Book.objects.first()
        self.assertTrue(book.chapters_count == 0)
        create_book_chapter(book, '2', 'Test title', 'Test text')
        self.assertTrue(book.chapters_count == 1)

    def test_add_book_booktag(self):
        tag_name = 'Test tag'
        book = Book.objects.first()
        self.assertFalse(book.booktag.all())
        create_book_tag(tag_name)
        add_book_booktag(book, tag_name)
        book_booktags = book.booktag.all()
        self.assertTrue(len(book_booktags) == 1)
        self.assertTrue(book_booktags[0].name == 'Test Tag')

    @factory.django.mute_signals(signals.post_save)
    def test_update_book_data(self):
        from ..scrapers import BookScraper
        book_scraper = BookScraper()
        book_url = 'https://www.webnovel.com/book/blood-warlock-succubus-partner-in-the-apocalypse_20134751006091605'
        book_data = book_scraper.webnovel_get_book_data(book_url, volumes=False)
        book = Book.objects.first()
        update_book_data(book, book_data, save=True)
        book = Book.objects.first()
        self.assertTrue('blood warlock' in book.title.lower())
        self.assertTrue(book.author)
        self.assertTrue(re.search(r'^posters.+jpg$', str(book.poster)))
        self.assertTrue(len(book.description) >= 100)
        self.assertTrue(len(book.booktag.all()) >= 3)
        self.assertTrue(book.visited)
        self.assertTrue(book.status == 1)
