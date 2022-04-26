from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from novel.books.models import Book, BookGenre, BookTag, BookChapter


class BookSitemap(Sitemap):
    priority = 1.0
    protocol = "https"

    def items(self):
        return Book.objects.published().order_by('pk')

    def lastmod(self, obj):
        return obj.modified


class BookGenreSitemap(Sitemap):
    protocol = "https"

    def items(self):
        return BookGenre.objects.order_by('pk')

    def lastmod(self, obj):
        return obj.modified


class BookTagSitemap(Sitemap):
    protocol = "https"

    def items(self):
        return BookTag.objects.order_by('pk')

    def lastmod(self, obj):
        return obj.modified


class BookChapterSitemap(Sitemap):
    priority = 0.7
    protocol = "https"

    def items(self):
        return BookChapter.objects.filter(c_id=1)

    def lastmod(self, obj):
        return obj.modified


class StaticViewSitemap(Sitemap):
    changefreq = "monthly"
    protocol = "https"

    def items(self):
        static_urls = ['books:front_page', 'contact-us', 'advertisement', 'send-feedback', 'report-problem', 'privacy-policy', 'terms-conditions']
        return static_urls

    def location(self, item):
        return reverse(item)
