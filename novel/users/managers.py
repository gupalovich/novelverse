from django.db import models
from django.contrib.auth.models import UserManager


class UserManager(UserManager):
    def get_queryset(self):
        return super().get_queryset().select_related('profile', 'library')
