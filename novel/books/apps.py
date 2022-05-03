from django.apps import AppConfig


class BooksConfig(AppConfig):
    name = 'novel.books'
    verbose_name = "books"

    def ready(self):
        try:
            import novel.books.signals  # noqa F401
        except ImportError:
            pass
