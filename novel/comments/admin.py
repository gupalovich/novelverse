from django.contrib import admin
from django.utils.translation import ugettext_lazy as _

from django_comments_xtd.admin import XtdCommentsAdmin
from .models import CustomComment
from django_comments import get_model
from django_comments.admin import CommentsAdmin
from django_comments.models import CommentFlag
from django_comments_xtd.models import XtdComment, BlackListedDomain


class CustomCommentAdmin(XtdCommentsAdmin):
    list_display = ('thread_level', 'user_avatar', 'cid', 'name', 'content_type',
                    'object_pk', 'submit_date', 'followup', 'is_public',
                    'is_removed')
    list_display_links = ('cid', 'user_avatar', )
    fieldsets = (
        (None, {'fields': ('content_type', 'object_pk', 'site')}),
        (_('Content'), {'fields': ('user', 'user_name', 'user_avatar', 'user_email', 'user_url', 'comment', 'followup')}),
        (_('Metadata'), {'fields': ('submit_date', 'ip_address', 'is_public', 'is_removed')}),
    )


class BlackListedDomainAdmin(admin.ModelAdmin):
    search_fields = ['domain']


if get_model() is CustomComment:
    admin.site.register(CustomComment, CustomCommentAdmin)
    # admin.site.register(XtdComment, XtdCommentsAdmin)
    admin.site.register(CommentFlag)
    admin.site.register(BlackListedDomain, BlackListedDomainAdmin)
