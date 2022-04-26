from django.db.models import Count
from django.contrib import admin
from django_summernote.admin import SummernoteModelAdminMixin
from .models import BookGenre, BookTag, Book, BookChapter


@admin.register(BookGenre)
class BookGenreAdmin(admin.ModelAdmin):
    search_fields = ('name', )
    list_display = ('name', 'get_bookcount', 'created', 'modified', )
    readonly_fields = ('slug', 'get_bookcount', 'created', 'modified', )

    fieldsets = (
        (None, {
            'fields': (('name', 'slug'), 'get_bookcount'),
        }),
        (None, {
            'fields': ('created', 'modified'),
        }),
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        qs = qs.prefetch_related('books').annotate(Count('book'))
        return qs

    def get_bookcount(self, obj):
        return obj.book__count
    get_bookcount.short_description = 'Books Count'
    get_bookcount.admin_order_field = 'book__count'


@admin.register(BookTag)
class BookTagAdmin(admin.ModelAdmin):
    search_fields = ('name', )
    list_display = ('name', 'get_bookcount', 'created', 'modified', )
    readonly_fields = ('slug', 'get_bookcount', 'created', 'modified', )
    fieldsets = (
        (None, {
            'fields': (('name', 'slug'), 'get_bookcount'),
        }),
        (None, {
            'fields': ('created', 'modified'),
        }),
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        qs = qs.prefetch_related('books').annotate(Count('books'))
        return qs

    def get_bookcount(self, obj):
        return obj.books__count
    get_bookcount.short_description = 'Books Count'
    get_bookcount.admin_order_field = 'books__count'


def update_recommended_true(modeladmin, request, qs):
    qs.update(recommended=True)


def update_recommended_false(modeladmin, request, qs):
    qs.update(recommended=False)


def update_status_draft(modeladmin, request, qs):
    qs.update(status=0)


def update_status_published(modeladmin, request, qs):
    qs.update(status=1)


def update_visited_true(modeladmin, request, qs):
    qs.update(visited=True)


def update_visited_false(modeladmin, request, qs):
    qs.update(visited=False)


def update_revisited_true(modeladmin, request, qs):
    qs.update(revisited=True)


def update_revisited_false(modeladmin, request, qs):
    qs.update(revisited=False)


@admin.register(Book)
class BookAdmin(SummernoteModelAdminMixin, admin.ModelAdmin):
    actions = [
        update_status_draft, update_status_published,
        update_recommended_true, update_recommended_false,
        update_visited_true, update_visited_false, update_revisited_true, update_revisited_false, ]
    search_fields = ('title', 'description', )
    fieldsets = (
        (None, {
            'fields': ((('title', 'title_sm', 'slug')), ),
        }),
        (None, {
            'fields': (('status', 'status_release'), ),
        }),
        (None, {
            'fields': ('bookgenre', 'booktag', ),
        }),
        ('Book info', {
            'classes': ('extrapretty'),
            'fields': (
                ('author', 'country', 'similar'),
                ('volumes', 'chapters_release', 'chapters_count'),
                ('rating', 'ranking', 'votes', 'recommended'),
                'poster', 'description'
            ),
        }),
        ('Scraping', {
            'fields': (
                ('visit', 'visit_id', 'visited'),
                ('revisit', 'revisit_id', 'revisited'),
            ),
        }),
    )
    summernote_fields = ('description', )
    readonly_fields = ('slug', 'chapters_count', )
    filter_horizontal = ('booktag', )
    list_select_related = ('bookgenre', )
    list_display = ('pk', 'title', 'get_bookgenre', 'recommended', 'chapters_count', 'status', 'visited', 'visit_id', 'revisited', 'revisit_id', 'created', 'modified', )
    list_display_links = ('pk', 'title')

    def get_bookgenre(self, obj):
        return obj.bookgenre.name
    get_bookgenre.short_description = 'Book Genre'
    get_bookgenre.admin_order_field = 'bookgenre'


@admin.register(BookChapter)
class BookChapterAdmin(SummernoteModelAdminMixin, admin.ModelAdmin):
    autocomplete_fields = ['book', ]
    search_fields = ('c_id', 'title', 'book__title', )
    fieldsets = (
        (None, {
            'fields': (
                'c_id',
                'book',
                'title',
                'slug',
                'text',
                'allow_comments',
            ),
        }),
        (None, {
            'fields': ('created', 'modified'),
        }),
    )
    summernote_fields = ('text', )
    readonly_fields = ('slug', 'c_id', 'created', 'modified')
    list_select_related = ('book', )
    list_display = ('title', 'c_id', 'get_book', 'get_book_visit_id', 'get_book_revisit_id', 'created', 'modified', )

    def get_book(self, obj):
        return obj.book.title
    get_book.short_description = 'Book'
    get_book.admin_order_field = 'book'

    def get_book_visit_id(self, obj):
        return obj.book.visit_id
    get_book_visit_id.short_description = 'Book visit_id'

    def get_book_revisit_id(self, obj):
        return obj.book.revisit_id
    get_book_revisit_id.short_description = 'Book revisit_id'
