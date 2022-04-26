from django.db import models
from django.contrib.postgres.fields import ArrayField
# from django.conf import settings
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _
from model_utils import Choices, FieldTracker
from model_utils.fields import MonitorField
from model_utils.models import TimeStampedModel

from .managers import BookManager
from .utils import get_unique_slug, capitalize_str


class BookGenre(TimeStampedModel):
    name = models.CharField(_('Genre'), blank=False, default='', max_length=112)
    slug = models.SlugField(max_length=112, unique=True)
    tracker = FieldTracker()

    class Meta:
        ordering = ['name']
        verbose_name = _('Book Genre')
        verbose_name_plural = _('Book Genres')

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('books:genre', kwargs={'bookgenre_slug': self.slug})

    def save(self, *args, **kwargs):
        self.name = capitalize_str(self.name)
        if not self.slug or self.name != self.tracker.previous('name'):
            self.slug = get_unique_slug(BookGenre, self.name)
        return super().save(*args, **kwargs)


class BookTag(TimeStampedModel):
    name = models.CharField(_('Tag'), blank=False, default='', max_length=112)
    slug = models.SlugField(max_length=112, unique=True)
    tracker = FieldTracker()

    class Meta:
        ordering = ['name']
        verbose_name = _('Book Tag')
        verbose_name_plural = _('Book Tags')

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('books:tag', kwargs={'booktag_slug': self.slug})

    def save(self, *args, **kwargs):
        self.name = capitalize_str(self.name)
        if not self.slug or self.name != self.tracker.previous('name'):
            self.slug = get_unique_slug(BookTag, self.name)
        return super().save(*args, **kwargs)


class Book(TimeStampedModel):
    objects = BookManager()
    title = models.CharField(_('Title'), blank=False, default='', max_length=255)
    title_sm = models.CharField(_('Title short'), blank=True, default='', max_length=50)
    slug = models.SlugField(default='', max_length=255, unique=True)
    bookgenre = models.ForeignKey(
        BookGenre,
        null=True,
        on_delete=models.SET_NULL,
        related_name='%(class)ss',
        related_query_name='%(class)s',
    )
    booktag = models.ManyToManyField(BookTag, related_name='%(class)ss', blank=True)
    author = ArrayField(models.CharField(max_length=112), blank=True, default=list)
    allow_comments = models.BooleanField('allow comments', default=True)
    COUNTRY_CHOICES = Choices(
        ('china', 'China'),
        ('korea', 'Korea'),
        ('japan', 'Japan'),
        ('original', 'Original')
    )
    country = models.CharField(choices=COUNTRY_CHOICES, blank=True, default=COUNTRY_CHOICES.china, max_length=55)
    similar = ArrayField(models.IntegerField(), blank=True, default=list)
    description = models.TextField(_('Description'), blank=True, default='')
    volumes = ArrayField(models.SmallIntegerField(default=1), blank=True, default=list)
    chapters_count = models.PositiveIntegerField(_('Chapters'), blank=True, null=True, default=0)
    chapters_release = models.SmallIntegerField(_('Chapters update'), blank=True, null=True, default=0)
    poster = models.ImageField(
        _('Poster'), blank=True, null=True,
        upload_to='posters/',
        default='posters/default.jpg'
    )
    votes = models.PositiveIntegerField(_('Votes'), blank=True, null=True, default=0)
    ranking = models.PositiveIntegerField(_('Ranking'), blank=True, null=True, default=0)
    rating = models.FloatField(_('Rating'), blank=True, default=0.0)
    recommended = models.BooleanField(blank=True, default=False)
    VISIT_CHOICES = Choices(
        ('webnovel', 'Webnovel'),
        ('boxnovel', 'Boxnovel'),
        ('wuxiaworld', 'Wuxia World'),
        ('gravitytails', 'Gravity Tails'),
        ('flyinglines', 'Flying Lines'),
        ('lnmtl', 'LNMTL'),
        ('other', 'Other'),
    )
    visit = models.CharField(
        choices=VISIT_CHOICES, blank=True, default=VISIT_CHOICES.webnovel, max_length=55)
    visit_id = models.CharField(_('Visit id'), blank=True, default='', max_length=255)
    visited = models.BooleanField(default=False, blank=True)
    revisit = models.CharField(
        choices=VISIT_CHOICES, blank=True, default=VISIT_CHOICES.webnovel, max_length=55)
    revisit_id = models.CharField(_('Revisit id'), blank=True, default='', max_length=255)
    revisited = models.BooleanField(default=False, blank=True)
    STATUS = Choices(
        (0, 'draft', _('draft')),
        (1, 'published', _('published')),
    )
    status = models.IntegerField(choices=STATUS, default=STATUS.draft, db_index=True)
    STATUS_RELEASE = Choices(
        (0, 'ongoing', _('ongoing')),
        (1, 'onhold', _('onhold')),
        (2, 'abandoned', _('abandoned')),
        (3, 'completed', _('completed')),
    )
    status_release = models.IntegerField(choices=STATUS_RELEASE, default=STATUS_RELEASE.ongoing)
    published_at = MonitorField(monitor='status', when=['published'])
    tracker = FieldTracker()

    class Meta:
        verbose_name = _('Book')
        verbose_name_plural = _('Books')

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('books:book', kwargs={'book_slug': self.slug})

    def save(self, *args, **kwargs):
        self.title = capitalize_str(self.title)
        if not self.title and self.title_sm:
            self.title = capitalize_str(self.title_sm)
        if not self.poster:
            self.poster = 'posters/default.jpg'
        if not self.slug or self.title != self.tracker.previous('title'):
            self.slug = get_unique_slug(Book, self.title)
        return super().save(*args, **kwargs)

    def update_chapters_count(self):
        c_count_prev = self.tracker.previous('chapters_count')
        c_count = self.bookchapters.count()
        if c_count_prev != c_count:
            self.chapters_count = c_count
            self.save()


class BookChapter(TimeStampedModel):
    book = models.ForeignKey(
        Book,
        on_delete=models.CASCADE,
        related_name='%(class)ss',
        related_query_name='%(class)s',
    )
    allow_comments = models.BooleanField('allow comments', default=True)
    c_id = models.IntegerField('Chapter ID', blank=True, null=True, default=0)
    title = models.CharField(_('Title'), blank=False, default='', max_length=255)
    slug = models.SlugField(default='', max_length=255, unique=True)
    text = models.TextField(blank=False, default='')

    class Meta:
        verbose_name = _('Book Chapter')
        verbose_name_plural = _('Book Chapters')

    def __str__(self):
        return f'Book: {self.book.title} - Chapter {self.c_id}: {self.title}'

    def get_absolute_url(self):
        return reverse('books:bookchapter', kwargs={
            'book_slug': self.book.slug, 'c_id': self.c_id})

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = get_unique_slug(BookChapter, self.title)
        self.title = capitalize_str(self.title)
        return super().save(*args, **kwargs)
