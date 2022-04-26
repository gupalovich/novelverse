from .models import BookGenre


def bookgenres_processor(request):
    bookgenres = BookGenre.objects.all()
    return {'bookgenres': bookgenres}
