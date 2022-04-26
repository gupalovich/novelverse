from django.test import TestCase
from django.urls import resolve


class BookGenreUrlTest(TestCase):
    def setUp(self):
        self.resolver_list = resolve('/category/all/')
        self.resolver_solo = resolve('/category/test-genre/')

    def test_bookgenre_resolve(self):
        self.assertEqual(self.resolver_list.view_name, 'books:genre-list')
        self.assertEqual(self.resolver_solo.view_name, 'books:genre')

    def test_bookgenre_resolve_invalid(self):
        self.assertNotEqual(self.resolver_list.view_name, '')
        self.assertNotEqual(self.resolver_solo.view_name, '')


class BookTagUrlTest(TestCase):
    def setUp(self):
        self.resolver_list = resolve('/tags/all/')
        self.resolver_solo = resolve('/tags/test-genre/')

    def test_bookgenre_resolve(self):
        self.assertEqual(self.resolver_list.view_name, 'books:tag-list')
        self.assertEqual(self.resolver_solo.view_name, 'books:tag')

    def test_bookgenre_resolve_invalid(self):
        self.assertNotEqual(self.resolver_list.view_name, '')
        self.assertNotEqual(self.resolver_solo.view_name, '')


class BookUrlTest(TestCase):
    def setUp(self):
        self.resolver = resolve('/books/test-book/')

    def test_book_resolve(self):
        self.assertEqual(self.resolver.view_name, 'books:book')

    def test_book_resolve_invalid(self):
        self.assertNotEqual(self.resolver.view_name, '')


class BookRankingUrlTest(TestCase):
    def setUp(self):
        self.resolver = resolve('/ranking/')

    def test_book_resolve(self):
        self.assertEqual(self.resolver.view_name, 'books:ranking')

    def test_book_resolve_invalid(self):
        self.assertNotEqual(self.resolver.view_name, '')


class BookSearchUrlTest(TestCase):
    def setUp(self):
        self.resolver = resolve('/search/')

    def test_book_resolve(self):
        self.assertEqual(self.resolver.view_name, 'books:search')

    def test_book_resolve_invalid(self):
        self.assertNotEqual(self.resolver.view_name, '')
