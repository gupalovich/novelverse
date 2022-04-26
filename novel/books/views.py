from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.contrib.postgres.search import SearchVector
from django.db.models import F
from django.http import JsonResponse, HttpResponse
# from django.utils.decorators import method_decorator
from django.urls import reverse
from django.shortcuts import render, redirect
from django.template.loader import render_to_string
# from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.vary import vary_on_headers
from django.views.generic import View, DetailView, ListView

from novel2read.apps.users.models import BookProgress
from .models import Book, BookTag, BookChapter
from .forms import BookSearchForm
from .filters import BookFilter
from .utils import capitalize_slug


class FrontPageView(View):
    def get(self, request, *args, **kwargs):
        books = Book.objects.published().select_related('bookgenre').filter(recommended=True).random_qslist(only=12)
        b_chaps = BookChapter.objects.order_by('book_id', '-created').distinct('book_id').values_list('id', flat=True)
        b_chaps = BookChapter.objects.select_related('book').filter(id__in=b_chaps).order_by('-created')
        promo_title = 'Read your favourite novels in one place'
        promo_subtitle = 'Get access to the latest releases of novels and light-novels'
        paginator = Paginator(b_chaps, 10)
        page = self.request.GET.get('page')
        b_chaps = paginator.get_page(page)
        context = {'books': books, 'b_chaps': b_chaps, 'promo_title': promo_title, 'promo_subtitle': promo_subtitle}

        return render(request, template_name='books/front_page.html', context=context)


class BookGenreView(ListView):
    template_name = 'books/bookgenre.html'

    def get(self, request, *args, **kwargs):
        p = 'page'
        p_num = 16
        try:
            # query params without page
            f_params = '&'.join({f'{k}={v}' if k != p else '' for (k, v) in request.GET.items()})
            f_params = '' if not f_params else '&' + f_params
            books = Book.objects.published().select_related('bookgenre').prefetch_related('booktag').order_by('-votes')
            if kwargs:
                books = books.filter(bookgenre__slug=kwargs['bookgenre_slug'])
            f = BookFilter(request.GET, queryset=books)
            paginator = Paginator(list(f.qs), p_num)
            page = request.GET.get(p)
            f_books = paginator.get_page(page)
            context = {
                'f_params': f_params,
                'f_form': f.form,
                'f_books': f_books,
            }
            return render(request, template_name=self.template_name, context=context)
        except Book.DoesNotExist:
            return redirect('/404/')


class BookTagView(ListView):
    template_name = 'books/booktag.html'

    def get(self, request, *args, **kwargs):
        p = 'page'
        p_num = 16
        try:
            tags = BookTag.objects.all()
            context = {'tags': tags}
            if kwargs:
                # query params without page
                f_params = '&'.join({f'{k}={v}' if k != p else '' for (k, v) in request.GET.items()})
                f_params = '' if not f_params else '&' + f_params
                tag_name = capitalize_slug(kwargs['booktag_slug'])
                books = Book.objects.published().filter(booktag__slug=kwargs['booktag_slug'])
                books = books.select_related('bookgenre').prefetch_related('booktag').order_by('-votes')
                f = BookFilter(request.GET, queryset=books)
                paginator = Paginator(list(f.qs), p_num)
                page = request.GET.get(p)
                f_books = paginator.get_page(page)
                context['tag_name'] = tag_name
                context['f_params'] = f_params
                context['f_form'] = f.form
                context['f_books'] = f_books
            return render(request, template_name=self.template_name, context=context)
        except BookTag.DoesNotExist:
            return redirect('/404/')


class BookView(DetailView):
    template_name = 'books/book.html'

    @vary_on_headers('X-Requested-With')
    def get(self, request, *args, **kwargs):
        try:
            book = Book.objects.select_related('bookgenre').prefetch_related('booktag').get(slug=kwargs['book_slug'])
            user_auth = request.user.is_authenticated

            if request.is_ajax():
                data = {}
                bookchapters = list(book.bookchapters.values_list(
                    'c_id', 'title', 'created', named=True).order_by('c_id'))
                last_chap = bookchapters[-1] if len(bookchapters) >= 1 else None
                template_name = 'books/book_chap_nav.html'
                context = {
                    'book': book,
                    'bookchapters': bookchapters,
                    'last_chap': last_chap,
                }
                data['html_chaps'] = render_to_string(
                    template_name,
                    context=context,
                    request=request
                )
                return JsonResponse(data)

            context = {
                'book': book,
                'next': reverse('comments-xtd-sent'),
                'user_auth': user_auth
            }
            if book.similar:
                similar_books = Book.objects.filter(id__in=book.similar).order_by('pk')
                context.update({'similar_books': similar_books})
            if user_auth:
                book_prog = False
                context['user_lib'] = list(request.user.library.book.all())
                try:
                    book_prog = BookProgress.objects.get(user=request.user, book=book)
                    context['book_prog'] = book_prog
                except BookProgress.DoesNotExist:
                    context['book_prog'] = book_prog
            return render(request, template_name=self.template_name, context=context)
        except Book.DoesNotExist:
            return redirect('/404/')


class BookChapterView(DetailView):
    template_name = 'books/bookchapter.html'

    @vary_on_headers('X-Requested-With')
    def get(self, request, *args, **kwargs):
        try:
            b_chap = BookChapter.objects.select_related('book').get(book__slug=kwargs['book_slug'], c_id=kwargs['c_id'])
            b_chaps = BookChapter.objects.filter(book__slug=kwargs['book_slug']).values('c_id', 'title', 'created').order_by('c_id')
            for chap in b_chaps:
                url = reverse('books:bookchapter', kwargs={'book_slug': b_chap.book.slug, 'c_id': chap['c_id']})
                chap.update({'absolute_url': url})

            try:
                prev_chap = b_chaps[kwargs['c_id'] - 2:kwargs['c_id'] - 1][0]
            except (IndexError, AssertionError):
                prev_chap = None
            try:
                next_chap = b_chaps[kwargs['c_id']:kwargs['c_id'] + 2][0]
            except IndexError:
                next_chap = None

            if request.is_ajax():
                data = {}
                template_name = 'books/bookchapter_chap_nav.html'
                context = {'b_chap': b_chap, 'b_chaps': b_chaps}
                data['html_chaps'] = render_to_string(
                    template_name,
                    context=context,
                    request=request
                )
                return JsonResponse(data)

            context = {
                'b_chap': b_chap,
                'prev_chap': prev_chap,
                'next_chap': next_chap,
            }

            if request.user.is_authenticated:
                context['user_lib'] = list(request.user.library.book.all())
                try:
                    book_prog = BookProgress.objects.get(user=request.user, book=b_chap.book)
                    if book_prog.c_id != b_chap.c_id:
                        book_prog.c_id = b_chap.c_id
                        book_prog.save()
                except BookProgress.DoesNotExist:
                    BookProgress.objects.create(
                        book=b_chap.book,
                        user=request.user,
                        c_id=b_chap.c_id,
                    )
            return render(request, template_name=self.template_name, context=context)
        except (Book.DoesNotExist, BookChapter.DoesNotExist):
            return redirect('/404/')


class BookRankingView(ListView):
    template_name = 'books/bookranking.html'
    queryset = Book.objects.published().filter(ranking__gt=0).order_by('ranking')
    context_object_name = 'books_all'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        qs = list(self.queryset.iterator())
        user_auth = self.request.user.is_authenticated
        books = qs[3:]
        books_top = qs[:3]
        paginator = Paginator(books, 7)
        page = self.request.GET.get('page')
        books = paginator.get_page(page)
        context = {
            'books': books, 'books_top': books_top,
            'page_title': 'Ranking',
            'user_auth': user_auth,
        }
        if user_auth:
            user_lib = list(self.request.user.library.book.all())
            context['user_lib'] = user_lib
        return context


class BookSearchView(ListView):
    template_name = 'books/booksearch.html'
    form = BookSearchForm
    context = {'form': form, 'page_title': 'Search Books'}

    def get(self, request, **kwargs):
        form = self.form(request.GET)
        context = dict(self.context)  # update get view context
        context['form'] = form

        if request.is_ajax():
            data = {}
            template_name = 'books/booksearch-result.html'
            search_field = request.GET.get('search_field', None)

            if not search_field:
                # handle ajax error
                return JsonResponse(data, status=403)

            books = Book.objects.published().select_related('bookgenre').annotate(
                search=SearchVector('title', 'description'),
            ).filter(search=search_field)
            context['books'] = books
            context['s_result'] = f"<p>Didn't find book: <b>{search_field}</b></p>" if not books else ''
            data['html_search_form_result'] = render_to_string(
                template_name,
                context=context,
                request=request
            )
            return JsonResponse(data)

        if form.is_valid():
            search_field = form.cleaned_data['search_field']
            books = Book.objects.published().select_related('bookgenre').annotate(
                search=SearchVector('title', 'description'),
            ).filter(search=search_field)
            context['s_result'] = f"<p>Didn't find book: <b>{search_field}</b></p>" if not books else ''
            context['books'] = books
            return render(request, template_name=self.template_name, context=context)
        else:
            return render(request, template_name=self.template_name, context=self.context)


@login_required
def book_vote_view(request, *args, **kwargs):
    if request.method == "POST":
        try:
            user = request.user
            book = Book.objects.get(slug=kwargs['book_slug'])
            book_rev = reverse('books:book', kwargs={'book_slug': kwargs['book_slug']})
            next_url = request.POST.get('next', book_rev)
            if user.profile.votes <= 0:
                print('user reached vote limit')
            else:
                user.profile.votes = F('votes') - 1
                user.save()
                book.votes = F('votes') + 1
                book.save()
            return redirect(next_url)
        except Book.DoesNotExist:
            return redirect('/404/')
    return redirect('/400/')


@login_required
def book_vote_ajax_view(request, *args, **kwargs):
    data = {'is_valid': False}

    if request.is_ajax():
        user = request.user
        user_votes = user.profile.votes
        book = Book.objects.get(slug=kwargs['book_slug'])
        if user_votes <= 0:
            data['info_msg'] = 'You are out of votes'
        else:
            try:
                data['is_valid'] = True
                data['user_votes'] = int(user_votes) - 1
                data['book_votes'] = int(book.votes) + 1
                user.profile.votes = F('votes') - 1
                user.save()
                book.votes = F('votes') + 1
                book.save(update_fields=['votes'])
            except Exception as e:
                data['error'] = str(e)
    return JsonResponse(data)


def session_theme_ajax_view(request, *args, **kwargs):
    data = {
        'state': 'pending',
        'error': {},
    }
    resp = JsonResponse(data)

    if request.is_ajax():
        max_age = 60 * 60 * 24 * 30 * 3
        default_color = request.COOKIES.get('tm_color', '')
        default_font = request.COOKIES.get('tm_font', '')
        default_fz = request.COOKIES.get('tm_fz', '')
        default_lh = request.COOKIES.get('tm_lh', '')
        theme_color = request.POST.get('tm_color', default_color)
        theme_font = request.POST.get('tm_font', default_font)
        theme_fz = request.POST.get('tm_fz', default_fz)
        theme_lh = request.POST.get('tm_lh', default_lh)
        resp.set_cookie('tm_color', theme_color, max_age=max_age)
        resp.set_cookie('tm_font', theme_font, max_age=max_age)
        resp.set_cookie('tm_fz', theme_fz, max_age=max_age)
        resp.set_cookie('tm_lh', theme_lh, max_age=max_age)
    return resp
