from django.test import Client, TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from ..models import BookGenre, BookTag, Book

User = get_user_model()


class FrontPageViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.response = self.client.get(reverse('books:front_page'))

    def test_frontpage_response(self):
        self.assertEqual(self.response.status_code, 200)

    def test_frontpage_response_invalid(self):
        self.assertNotEqual(self.response.status_code, 404)

    def test_frontpage_content(self):
        self.assertIn('html', self.response.content.decode('utf-8'))

    def test_frontpage_content_invalid(self):
        self.assertNotEqual(self.response.content.decode('utf-8'), {})


class GenrePageViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.bookgenre = BookGenre.objects.create(name='test genre')
        self.bookgenre_1 = BookGenre.objects.create(name='test genre other')
        self.book = Book.objects.create(title='test book', bookgenre=self.bookgenre, status=1)
        self.book_1 = Book.objects.create(title='test book other', bookgenre=self.bookgenre_1, status=1)
        self.response_list = self.client.get(reverse('books:genre-list'))
        self.response_solo = self.client.get(
            reverse('books:genre', kwargs={'bookgenre_slug': self.bookgenre.slug}))

    def test_bookgenre_response(self):
        self.assertEqual(self.response_list.status_code, 200)
        self.assertEqual(self.response_solo.status_code, 200)

    def test_bookgenre_response_invalid(self):
        self.assertNotEqual(self.response_list.status_code, 404)
        self.assertNotEqual(self.response_solo.status_code, 404)

    def test_bookgenre_content(self):
        self.assertIn('html', self.response_list.content.decode('utf-8'))
        self.assertIn(self.book.title, self.response_list.content.decode('utf-8'))
        self.assertIn(self.book_1.title, self.response_list.content.decode('utf-8'))
        self.assertIn(self.book.title, self.response_solo.content.decode('utf-8'))
        self.assertNotIn(self.book_1.title, self.response_solo.content.decode('utf-8'))
        self.assertIn(self.bookgenre.name, self.response_solo.content.decode('utf-8'))

    def test_bookgenre_content_invalid(self):
        self.assertNotEqual(self.response_list.content.decode('utf-8'), {})
        self.assertNotEqual(self.response_solo.content.decode('utf-8'), {})


class TagPageViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.bookgenre = BookGenre.objects.create(name='test genre')
        self.booktag = BookTag.objects.create(name='test tag')
        self.booktag_1 = BookTag.objects.create(name='test tag other')
        self.book = Book.objects.create(title='test book', bookgenre=self.bookgenre, status=1)
        self.book.booktag.add(self.booktag, self.booktag_1)
        self.response_list = self.client.get(reverse('books:tag-list'))
        self.response_solo = self.client.get(
            reverse('books:tag', kwargs={'booktag_slug': self.booktag.slug}))

    def test_booktag_response(self):
        self.assertEqual(self.response_list.status_code, 200)
        self.assertEqual(self.response_solo.status_code, 200)

    def test_booktag_response_invalid(self):
        self.assertNotEqual(self.response_list.status_code, 404)
        self.assertNotEqual(self.response_solo.status_code, 404)

    def test_booktag_content(self):
        self.assertIn('html', self.response_list.content.decode('utf-8'))
        self.assertIn(self.booktag.name, self.response_list.content.decode('utf-8'))
        self.assertIn(self.booktag_1.name, self.response_list.content.decode('utf-8'))
        self.assertIn(self.book.title, self.response_solo.content.decode('utf-8'))
        self.assertIn(self.booktag.name, self.response_solo.content.decode('utf-8'))

    def test_booktag_content_invalid(self):
        self.assertNotEqual(self.response_list.content.decode('utf-8'), {})
        self.assertNotEqual(self.response_solo.content.decode('utf-8'), {})


class BookViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.bookgenre = BookGenre.objects.create(name='test genre')
        self.booktag = BookTag.objects.create(name='test tag')
        self.book = Book.objects.create(title='test book', bookgenre=self.bookgenre, status=1)
        self.book.booktag.add(self.booktag)
        self.response = self.client.get(reverse('books:book', kwargs={'book_slug': self.book.slug}))

    def test_book_response(self):
        self.assertEqual(self.response.status_code, 200)

    def test_book_response_invalid(self):
        self.assertNotEqual(self.response.status_code, 404)

    def test_book_content(self):
        self.assertIn('html', self.response.content.decode('utf-8'))
        self.assertIn(self.book.bookgenre.name, self.response.content.decode('utf-8'))
        self.assertIn(self.book.title, self.response.content.decode('utf-8'))
        self.assertIn(self.booktag.name, self.response.content.decode('utf-8'))


class BookRankingViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.bookgenre = BookGenre.objects.create(name='test genre')
        self.book = Book.objects.create(title='test book one', bookgenre=self.bookgenre, votes=134, status=1, ranking=1)
        self.book_1 = Book.objects.create(title='test book two', bookgenre=self.bookgenre, votes=74, status=1, ranking=2)
        self.book_2 = Book.objects.create(title='test book three', bookgenre=self.bookgenre, votes=34, status=1, ranking=3)
        self.response = self.client.get(reverse('books:ranking'))

    def test_bookranking_response(self):
        self.assertEqual(self.response.status_code, 200)

    def test_bookranking_response_invalid(self):
        self.assertNotEqual(self.response.status_code, 404)

    def test_bookranking_content(self):
        self.assertIn('html', self.response.content.decode('utf-8'))
        self.assertIn(self.book.title, self.response.content.decode('utf-8'))
        self.assertIn(self.book_1.title, self.response.content.decode('utf-8'))
        self.assertIn(self.book_2.title, self.response.content.decode('utf-8'))


class BookSearchViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.book = Book.objects.create(title='test unique', status=1)
        self.book_1 = Book.objects.create(title='test antique', status=1)
        self.book_2 = Book.objects.create(title='monique', status=1)
        self.rev_bs = reverse('books:search')
        self.resp = self.client.get(self.rev_bs)

    def test_book_response(self):
        self.assertEqual(self.resp.status_code, 200)

    def test_book_search_result(self):
        resp = self.client.get(reverse('books:search'), {'search_field': 'test'})
        self.assertIn(self.book.title, resp.content.decode('utf-8'))
        self.assertIn(self.book_1.title, resp.content.decode('utf-8'))
        resp = self.client.get(reverse('books:search'), {'search_field': 'moniqu'})
        self.assertIn(self.book_2.title, resp.content.decode('utf-8'))

    def test_book_search_ajax(self):
        resp = self.client.get(reverse('books:search'), {'search_field': 'test'}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        resp_content = str(resp.content, encoding='utf8')
        self.assertEqual(resp.status_code, 200)
        self.assertIn('html_search_form_result', resp_content)


class BookVoteViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='test', password='test')
        self.book = Book.objects.create(title='test book')
        self.bookgenre = BookGenre.objects.create(name='test genre')
        self.client.login(username='test', password='test')
        self.resp = self.client.post(reverse('books:vote', kwargs={'book_slug': self.book.slug}))
        self.rev_book = reverse('books:book', kwargs={'book_slug': self.book.slug})
        self.rev_vote = reverse('books:vote', kwargs={'book_slug': self.book.slug})
        self.rev_vote_ajax = reverse('books:vote-ajax', kwargs={'book_slug': self.book.slug})
        self.rev_ranking = reverse('books:ranking')
        self.rev_session_theme_ajax = reverse('books:session-theme-ajax')

    def test_book_votes(self):
        self.book.refresh_from_db()
        self.user.refresh_from_db()
        self.assertRedirects(self.resp, self.rev_book)
        self.assertEqual(self.book.votes, 1)
        self.assertEqual(self.user.profile.votes, 2)

        resp = self.client.post(self.rev_vote, {'next': self.rev_ranking})
        self.book.refresh_from_db()
        self.user.refresh_from_db()
        self.assertRedirects(resp, self.rev_ranking)
        self.assertEqual(self.book.votes, 2)
        self.assertEqual(self.user.profile.votes, 1)

    def test_book_ajax_vote(self):
        resp = self.client.post(self.rev_vote_ajax, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(resp.status_code, 200)
        self.assertJSONEqual(
            str(resp.content, encoding='utf8'),
            {'is_valid': True, 'user_votes': 1, 'book_votes': 2}
        )

    def test_session_theme_ajax_view(self):
        resp = self.client.post(
            self.rev_session_theme_ajax,
            {
                'tm_color': 'tm-color-dark',
                'tm_font': 'tm-font-std',
                'tm_fz': 'tm-fz-15',
                'tm-lh': 'tm-lh-15',
            },
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.assertEqual(resp.status_code, 200)
        self.assertJSONEqual(
            str(resp.content, encoding='utf8'),
            {'state': 'pending', 'error': {}}
        )
