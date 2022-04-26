from django.apps import AppConfig


class CommentsConfig(AppConfig):
    name = 'novel.comments'
    verbose_name = "comments"

    def ready(self):
        try:
            import novel2read.apps.comments.signals  # noqa F401
        except ImportError:
            pass
