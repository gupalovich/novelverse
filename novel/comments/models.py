from django.db import models
from django_comments_xtd.models import XtdComment

from .managers import CustomCommentManager


class CustomComment(XtdComment):
    user_avatar = models.CharField(default='users/default.png', blank=True, max_length=255)
