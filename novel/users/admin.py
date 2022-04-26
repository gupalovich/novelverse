from django.contrib import admin
from django.contrib.auth import admin as auth_admin
from django.contrib.auth import get_user_model

from novel.users.forms import UserChangeForm, UserCreationForm
from novel.users.models import Profile, Library, BookProgress

User = get_user_model()


class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False


class LibraryInline(admin.StackedInline):
    model = Library
    filter_horizontal = ('book', )
    can_delete = False


@admin.register(User)
class UserAdmin(auth_admin.UserAdmin):
    inlines = (ProfileInline, LibraryInline, )
    form = UserChangeForm
    add_form = UserCreationForm
    fieldsets = (("User", {"fields": ("name",)}),) + auth_admin.UserAdmin.fieldsets
    list_select_related = ('library', 'profile')
    list_display = ["username", "name", "profile_premium", "is_superuser"]
    search_fields = ["name"]

    def profile_premium(self, instance):
        return instance.profile.premium
    profile_premium.short_description = 'Premium'
    profile_premium.boolean = True


@admin.register(BookProgress)
class BookProgressAdmin(admin.ModelAdmin):
    search_fields = ('user__username', 'book__title', )
    fields = ('user', 'book', 'c_id')
    list_select_related = ('book',)
    list_display = ('user', 'book', 'c_id')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        qs = qs.prefetch_related('user')
        return qs
