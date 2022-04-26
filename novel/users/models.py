import uuid
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.db import models
from django.db.models import CharField
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from .managers import UserManager
from novel.books.models import Book


class User(AbstractUser):
    # First Name and Last Name do not cover name patterns
    # around the globe.
    objects = UserManager()
    name = CharField(_("Name of User"), blank=True, max_length=255)

    def get_absolute_url(self):
        return reverse("users:detail", kwargs={"username": self.username})


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_profile_library(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
        Library.objects.create(user=instance)


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def save_user_profile_library(sender, instance, **kwargs):
    instance.profile.save()
    instance.library.save()


class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, primary_key=True)
    avatar = models.ImageField(
        _('Avatar'), blank=True, null=True,
        upload_to='users/',
        default='users/default.png'
    )
    bio = models.TextField(max_length=500, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    location = models.CharField(max_length=100, blank=True)
    premium = models.BooleanField(default=False, blank=True)
    premium_expire = models.DateTimeField(null=True, blank=True)
    votes = models.IntegerField(_('Votes'), blank=True, null=True, default=3)

    class Meta:
        verbose_name = _('Profile')
        verbose_name_plural = _('Profile data')


@receiver(post_save, sender=Profile)
def update_blank_avatar(sender, instance, created=False, **kwargs):
    if not instance.avatar:
        instance.avatar = 'users/default.png'
        instance.save()


class Library(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, primary_key=True)
    book = models.ManyToManyField(Book, related_name='%(class)ss', blank=True)

    class Meta:
        verbose_name = _('Library')
        verbose_name_plural = _('Library data')

    def __str__(self):
        return self.user.username


class BookProgress(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True, related_name='%(class)ses')
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='%(class)ses')
    c_id = models.IntegerField('Progress ID', blank=True, null=True, default=0, db_index=True)
    created = models.DateTimeField(auto_now_add=True, blank=True)
    updated = models.DateTimeField(auto_now=True, blank=True, null=True)

    class Meta:
        verbose_name = 'Book Progress'
        verbose_name_plural = 'Book Progresses'

    def __str__(self):
        return f'{self.user}: {self.book.title} Chapter {self.c_id}'
