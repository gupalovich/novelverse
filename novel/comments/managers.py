from django.db import models
from django_comments_xtd.models import XtdCommentManager


class CustomCommentManager(XtdCommentManager):
    def get_queryset(self, **kwargs):
        return super().get_queryset()
