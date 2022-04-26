from django.urls import path

from novel.users.views import (
    user_list_view,
    user_redirect_view,
    user_update_view,
    user_detail_view,
    library_view,
    add_library_book,
    remove_library_book,
    add_remove_library_book_ajax,
)

app_name = "users"
urlpatterns = [
    path("", view=user_list_view, name="list"),
    path("~redirect/", view=user_redirect_view, name="redirect"),
    path("~update/", view=user_update_view, name="update"),
    path("<str:username>/", view=user_detail_view, name="detail"),
    path("<str:username>/library/", view=library_view, name="library"),
    path("library/<slug:book_slug>/add/", view=add_library_book, name="library-add"),
    path("library/<slug:book_slug>/remove/", view=remove_library_book, name="library-remove"),
    path("library/<slug:book_slug>/lib-add-remove-ajax/", view=add_remove_library_book_ajax, name="lib-add-remove-ajax")
]
