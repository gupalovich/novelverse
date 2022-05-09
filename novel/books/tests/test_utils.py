from django.test import TestCase

from ..models import Book, BookGenre, BookChapter
from ..utils import (capitalize_str, capitalize_slug, multiple_replace, spoon_feed)


class UtilsTest(TestCase):
    def setUp(self):
        self.bookgenre = BookGenre.objects.create(name='test genre')
        self.slug = 'some-slug-123'
        self.string = 'some string 123'
        self.to_repl = {'<p>': '', '</p>': '', '  ': '', '\n': ''}
        self.text = "'<p>\n</p>\n\n\n    \n     sweat.\n\n\n    \n    \n</p>"
        self.book = Book.objects.create(title='test book', bookgenre=self.bookgenre, status=1)
        self.bookgenre = BookGenre.objects.create(name='test genre')

    def test_capitalize_slug(self):
        self.assertEqual('Some Slug', capitalize_slug(self.slug))

    def test_capitalize_string(self):
        self.assertEqual('Some String 123', capitalize_str(self.string))

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
        for i in range(100):
            Book.objects.create(title=f'test {i}', bookgenre=self.bookgenre)
        books = Book.objects.all()
        [i for i in spoon_feed(books, self.update_book_title, chunk=10)]
        self.assertEqual('Changed', Book.objects.first().title)
        self.assertEqual('Changed', Book.objects.last().title)
