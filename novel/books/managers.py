from random import sample
from django.db import models


class BookQuerySet(models.QuerySet):
    def published(self):
        return self.filter(status=1)

    def random_qslist(self, only=10):
        qs_list = list(self)
        qs_list = sample(qs_list, len(qs_list))[:only]
        return qs_list


class BookManager(models.Manager):
    def get_queryset(self):
        return BookQuerySet(self.model, using=self._db)

    def published(self, **kwargs):
        return self.get_queryset().published()

    def random_qslist(self, **kwargs):
        return self.get_queryset().random_qslist(only=kwargs.get('only', 10))
