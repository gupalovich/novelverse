# from django.contrib.auth import get_user_model
# from django.db.models.signals import post_save
# from django.dispatch import receiver
# from django_comments_xtd.models import XtdComment
# from .models import BasicComment

# User = get_user_model()


# @receiver(post_save, sender=XtdComment)
# def update_xtdcomment_user(sender, instance, created=False, **kwargs):
#     user = User.objects.get(pk=instance.user)
