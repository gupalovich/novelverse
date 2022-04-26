from django.test import TestCase
from django.urls import reverse

from ..models import BookGenre, BookTag, Book, BookChapter


def capitalize(str):
    return ' '.join([w.capitalize() for w in str.split(' ')])


class BookGenreModelTest(TestCase):
    def setUp(self):
        self.bookgenre = BookGenre.objects.create(name='test genre')
        self.bookgenre_1 = BookGenre.objects.create(name='test genre')

    def test_bookgenre_data(self):
        self.assertEqual(self.bookgenre.name, capitalize('test genre'))
        self.assertEqual(self.bookgenre.slug, 'test-genre')
        self.assertEqual(self.bookgenre_1.name, capitalize('test genre'))
        self.assertEqual(self.bookgenre_1.slug, 'test-genre-1')

    def test_bookgenre_data_invalid(self):
        self.assertNotEqual(self.bookgenre.name, '')
        self.assertNotEqual(self.bookgenre.slug, '')
        self.assertNotEqual(self.bookgenre_1.name, '')
        self.assertNotEqual(self.bookgenre_1.slug, '')

    def test_bookgenre_abs_url(self):
        abs_url = self.bookgenre.get_absolute_url()
        abs_url_1 = self.bookgenre_1.get_absolute_url()
        reverse_url = reverse('books:genre', kwargs={'bookgenre_slug': self.bookgenre.slug})
        reverse_url_1 = reverse('books:genre', kwargs={'bookgenre_slug': self.bookgenre_1.slug})

        self.assertEqual(abs_url, reverse_url)
        self.assertEqual(abs_url_1, reverse_url_1)

    def test_bookgenre_abs_url_invalid(self):
        abs_url = self.bookgenre.get_absolute_url()
        reverse_url = reverse('books:genre', kwargs={'bookgenre_slug': self.bookgenre.slug})

        self.assertNotEqual(abs_url, '')
        self.assertNotEqual(reverse_url, '')

    def test_bookgenre_save_unique_slug(self):
        self.assertEqual(self.bookgenre.slug, 'test-genre')
        self.assertEqual(self.bookgenre_1.slug, 'test-genre-1')
        self.bookgenre.name = 'test new genre'
        self.bookgenre.save()
        self.bookgenre_1.name = 'test new genre'
        self.bookgenre_1.save()
        self.assertEqual(self.bookgenre.slug, 'test-new-genre')
        self.assertEqual(self.bookgenre_1.slug, 'test-new-genre-1')

    def test_bookgenre_save_unique_slug_invalid(self):
        self.assertEqual(self.bookgenre.slug, 'test-genre')
        self.assertEqual(self.bookgenre_1.slug, 'test-genre-1')
        self.bookgenre.name = 'test new genre'
        self.bookgenre.save()
        self.bookgenre_1.name = 'test new genre'
        self.bookgenre_1.save()
        self.assertNotEqual(self.bookgenre.slug, 'test-genre')
        self.assertNotEqual(self.bookgenre_1.slug, 'test-genre-1')


class BookTagModelTest(TestCase):
    def setUp(self):
        self.booktag = BookTag.objects.create(name='test tag')
        self.booktag_1 = BookTag.objects.create(name='test tag')

    def test_booktag_data(self):
        self.assertEqual(self.booktag.name, capitalize('test tag'))
        self.assertEqual(self.booktag.slug, 'test-tag')
        self.assertEqual(self.booktag_1.name, capitalize('test tag'))
        self.assertEqual(self.booktag_1.slug, 'test-tag-1')

    def test_booktag_data_invalid(self):
        self.assertNotEqual(self.booktag.name, '')
        self.assertNotEqual(self.booktag.slug, '')
        self.assertNotEqual(self.booktag_1.name, '')
        self.assertNotEqual(self.booktag_1.slug, '')

    def test_booktag_abs_url(self):
        abs_url = self.booktag.get_absolute_url()
        abs_url_1 = self.booktag_1.get_absolute_url()
        reverse_url = reverse('books:tag', kwargs={'booktag_slug': self.booktag.slug})
        reverse_url_1 = reverse('books:tag', kwargs={'booktag_slug': self.booktag_1.slug})
        self.assertEqual(abs_url, reverse_url)
        self.assertEqual(abs_url_1, reverse_url_1)

    def test_booktag_abs_url_invalid(self):
        abs_url = self.booktag.get_absolute_url()
        reverse_url = reverse('books:tag', kwargs={'booktag_slug': self.booktag.slug})
        self.assertNotEqual(abs_url, '')
        self.assertNotEqual(reverse_url, '')

    def test_booktag_save_unique_slug(self):
        self.assertEqual(self.booktag.slug, 'test-tag')
        self.assertEqual(self.booktag_1.slug, 'test-tag-1')
        self.booktag.name = 'test new tag'
        self.booktag.save()
        self.booktag_1.name = 'test new tag'
        self.booktag_1.save()
        self.assertEqual(self.booktag.slug, 'test-new-tag')
        self.assertEqual(self.booktag_1.slug, 'test-new-tag-1')

    def test_booktag_save_unique_slug_invalid(self):
        self.assertEqual(self.booktag.slug, 'test-tag')
        self.assertEqual(self.booktag_1.slug, 'test-tag-1')
        self.booktag.name = 'test new tag'
        self.booktag.save()
        self.booktag_1.name = 'test new tag'
        self.booktag_1.save()
        self.assertNotEqual(self.booktag.slug, 'test-tag')
        self.assertNotEqual(self.booktag_1.slug, 'test-tag-1')


class BookModelTest(TestCase):
    def setUp(self):
        self.bookgenre = BookGenre.objects.create(name='test genre')
        self.booktag = BookTag.objects.create(name='test tag')
        self.booktag_1 = BookTag.objects.create(name='test tag 1')
        self.book = Book.objects.create(title='test book', bookgenre=self.bookgenre)
        self.book_1 = Book.objects.create(title='test book', bookgenre=self.bookgenre)
        self.book.booktag.add(self.booktag, self.booktag_1)
        self.book_1.booktag.add(self.booktag)

    def test_book_data(self):
        self.assertEqual(self.book.title, capitalize('test book'))
        self.assertEqual(self.book.slug, 'test-book')
        self.assertEqual(self.book_1.title, capitalize('test book'))
        self.assertEqual(self.book_1.slug, 'test-book-1')

    def test_book_data_invalid(self):
        self.assertNotEqual(self.book.title, '')
        self.assertNotEqual(self.book.slug, '')
        self.assertNotEqual(self.book_1.title, '')
        self.assertNotEqual(self.book_1.slug, '')

    def test_book_abs_url(self):
        abs_url = self.book.get_absolute_url()
        abs_url_1 = self.book_1.get_absolute_url()
        reverse_url = reverse('books:book', kwargs={'book_slug': self.book.slug})
        reverse_url_1 = reverse('books:book', kwargs={'book_slug': self.book_1.slug})
        self.assertEqual(abs_url, reverse_url)
        self.assertEqual(abs_url_1, reverse_url_1)

    def test_book_abs_url_invalid(self):
        abs_url = self.book.get_absolute_url()
        reverse_url = reverse('books:book', kwargs={'book_slug': self.book.slug})
        self.assertNotEqual(abs_url, '')
        self.assertNotEqual(reverse_url, '')

    def test_book_save_unique_slug(self):
        self.assertEqual(self.book.slug, 'test-book')
        self.assertEqual(self.book_1.slug, 'test-book-1')
        self.book.title = 'test new book'
        self.book.save()
        self.book_1.title = 'test new book'
        self.book_1.save()
        self.assertEqual(self.book.slug, 'test-new-book')
        self.assertEqual(self.book_1.slug, 'test-new-book-1')

    def test_book_save_unique_slug_invalid(self):
        self.assertEqual(self.book.slug, 'test-book')
        self.assertEqual(self.book_1.slug, 'test-book-1')
        self.book.title = 'test new book'
        self.book.save()
        self.book_1.title = 'test new book'
        self.book_1.save()
        self.assertNotEqual(self.book.slug, 'test-book')
        self.assertNotEqual(self.book_1.slug, 'test-book-1')

    def test_movie_tag_m2m(self):
        book_taglist = list(self.book.booktag.all())
        book_taglist_1 = list(self.book_1.booktag.all())
        self.assertEqual(len(book_taglist), 2)
        self.assertEqual(len(book_taglist_1), 1)
        self.assertEqual(book_taglist[0].name, capitalize('test tag'))
        self.assertEqual(book_taglist[-1].name, capitalize('test tag 1'))
        self.assertEqual(book_taglist_1[0].name, capitalize('test tag'))
        # m2m remove test
        self.book.booktag.remove(book_taglist[0])
        book_taglist = list(self.book.booktag.all())
        self.assertEqual(len(book_taglist), 1)
        self.assertEqual(book_taglist[0].name, capitalize('test tag 1'))


class BookChapterTest(TestCase):
    def setUp(self):
        self.book = Book.objects.create(title='test book')
        self.book_1 = Book.objects.create(title='test book 1')
        self.bookchapter = BookChapter.objects.create(title='test chapter', book=self.book)
        self.bookchapter_1 = BookChapter.objects.create(title='test chapter', book=self.book_1)

    def test_book_data(self):
        self.assertEqual(self.bookchapter.title, capitalize('test chapter'))
        self.assertEqual(self.bookchapter.book.title, capitalize('test book'))
        self.assertEqual(self.bookchapter_1.title, capitalize('test chapter'))
        self.assertEqual(self.bookchapter_1.book.title, capitalize('test book 1'))

    def test_book_data_invalid(self):
        self.assertNotEqual(self.bookchapter.title, '')
        self.assertNotEqual(self.bookchapter.slug, '')
        self.assertNotEqual(self.bookchapter.book.title, '')
        self.assertNotEqual(self.bookchapter_1.title, '')
        self.assertNotEqual(self.bookchapter_1.slug, '')
        self.assertNotEqual(self.bookchapter_1.book.title, '')

    def test_book_abs_url(self):
        abs_url = self.bookchapter.get_absolute_url()
        abs_url_1 = self.bookchapter_1.get_absolute_url()
        reverse_url = reverse(
            'books:bookchapter',
            kwargs={'book_slug': self.book.slug, 'c_id': self.bookchapter.c_id})
        reverse_url_1 = reverse(
            'books:bookchapter',
            kwargs={'book_slug': self.book_1.slug, 'c_id': self.bookchapter_1.c_id})
        self.assertEqual(abs_url, reverse_url)
        self.assertEqual(abs_url_1, reverse_url_1)

    def test_book_abs_url_invalid(self):
        abs_url = self.book.get_absolute_url()
        reverse_url = reverse(
            'books:bookchapter',
            kwargs={'book_slug': self.book.slug, 'c_id': self.bookchapter.c_id})
        self.assertNotEqual(abs_url, '')
        self.assertNotEqual(reverse_url, '')

    def test_update_chapters_cid(self):
        # bookchapter + 2 new chapters for book 1
        # book
        bookchapter_1 = BookChapter.objects.create(title='test chapter 1', book=self.book)
        bookchapter_2 = BookChapter.objects.create(title='test chapter 2', book=self.book)
        self.assertEqual(self.bookchapter.book.chapters_count, 3)
        self.assertEqual(self.bookchapter.c_id, 1)
        self.assertEqual(bookchapter_1.c_id, 2)
        self.assertEqual(bookchapter_2.c_id, 3)
        #   book_1
        bookchapter_11 = BookChapter.objects.create(title='test chapter 11', book=self.book_1)
        bookchapter_22 = BookChapter.objects.create(title='test chapter 22', book=self.book_1)
        self.assertEqual(self.bookchapter_1.book.chapters_count, 3)
        self.assertEqual(self.bookchapter_1.c_id, 1)
        self.assertEqual(bookchapter_11.c_id, 2)
        self.assertEqual(bookchapter_22.c_id, 3)

        # delete first and second BC
        self.bookchapter.delete()
        bookchapter_1.delete()
        self.assertEqual(bookchapter_2.book.chapters_count, 1)
        #   book_1
        self.bookchapter_1.delete()
        bookchapter_11.delete()
        self.assertEqual(bookchapter_22.book.chapters_count, 1)

        # create 2 new bc
        bookchapter_3 = BookChapter.objects.create(title='test chapter 3', book=self.book)
        bookchapter_4 = BookChapter.objects.create(title='test chapter 4', book=self.book)
        self.assertEqual(bookchapter_3.c_id, 2)
        self.assertEqual(bookchapter_4.c_id, 3)
        #   book_1
        bookchapter_33 = BookChapter.objects.create(title='test chapter 33', book=self.book_1)
        bookchapter_44 = BookChapter.objects.create(title='test chapter 44', book=self.book_1)
        self.assertEqual(bookchapter_33.c_id, 2)
        self.assertEqual(bookchapter_44.c_id, 3)
