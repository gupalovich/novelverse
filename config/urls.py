from django.conf import settings
from django.urls import include, path
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.views import defaults as default_views
from django.views.generic import TemplateView

from config.sitemaps import (
    BookSitemap,
    BookGenreSitemap,
    BookTagSitemap,
    BookChapterSitemap,
    StaticViewSitemap,
)
from .www_verif import GoogleSearchVerif, YandexSearchVerif

sitemaps = {
    'books': BookSitemap,
    'bookgenres': BookGenreSitemap,
    'booktags': BookTagSitemap,
    'bookchapters': BookChapterSitemap,
    'static_urls': StaticViewSitemap,
}

urlpatterns = [
    # Django Admin, use {% url 'admin:index' %}
    path(settings.ADMIN_URL, admin.site.urls),
    # Sitemap
    # path('sitemap.xml', cache_page(86400)(sitemap), {'sitemaps': sitemaps},
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
    # Search verification
    path(f'google{settings.WEBMASTER_VERIFICATION["google"]}.html', GoogleSearchVerif.as_view()),
    path(f'yandex_{settings.WEBMASTER_VERIFICATION["yandex"]}.html', YandexSearchVerif.as_view()),
    # User management
    path(
        "users/",
        include("novel.users.urls", namespace="users"),
    ),
    path("accounts/", include("allauth.urls")),
    path("comments/", include("django_comments_xtd.urls")),
    path("summernote/", include("django_summernote.urls")),
    # Your stuff: custom urls includes go here
    path("", include("novel.books.urls")),
    path("contact-us/", TemplateView.as_view(template_name='pages/contact-us.html'), name='contact-us'),
    path("advertisement/", TemplateView.as_view(template_name='pages/advertisement.html'), name='advertisement'),
    path("send-feedback/", TemplateView.as_view(template_name='pages/send-feedback.html'), name='send-feedback'),
    path("report-problem/", TemplateView.as_view(template_name='pages/report-problem.html'), name='report-problem'),
    path("privacy-policy/", TemplateView.as_view(template_name='pages/privacy-policy.html'), name='privacy-policy'),
    path("terms-conditions/", TemplateView.as_view(template_name='pages/terms-conditions.html'), name='terms-conditions'),
] + static(
    settings.MEDIA_URL, document_root=settings.MEDIA_ROOT
)

if settings.DEBUG:
    # This allows the error pages to be debugged during development, just visit
    # these url in browser to see how these error pages look like.
    urlpatterns += [
        path(
            "400/",
            default_views.bad_request,
            kwargs={"exception": Exception("Bad Request!")},
        ),
        path(
            "403/",
            default_views.permission_denied,
            kwargs={"exception": Exception("Permission Denied")},
        ),
        path(
            "404/",
            default_views.page_not_found,
            kwargs={"exception": Exception("Page not Found")},
        ),
        path("500/", default_views.server_error),
    ]
    if "debug_toolbar" in settings.INSTALLED_APPS:
        import debug_toolbar

        urlpatterns = [path("__debug__/", include(debug_toolbar.urls))] + urlpatterns
