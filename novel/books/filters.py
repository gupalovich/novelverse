from django_filters import FilterSet, ChoiceFilter

from .models import Book


class BookFilter(FilterSet):
    COUNTRY_CHOICES = (
        ('all', 'All'),
        ('china', 'China'),
        ('korea', 'Korea'),
        ('japan', 'Japan'),
    )
    CHAPTER_FILTER = (
        ('high', 'Highest'),
        ('low', 'Lowest'),
    )
    VOTES_FILTER = (
        ('high', 'Highest'),
        ('low', 'Lowest'),
    )
    RATING_FILTER = (
        ('all', 'All'),
        (1, 'atleast 1 star'),
        (2, 'atleast 2 star'),
        (3, 'atleast 3 star'),
        (4, 'atleast 4 star'),
    )

    # status_release = ChoiceFilter()
    country = ChoiceFilter(label='Country', choices=COUNTRY_CHOICES, method='filter_by_country')
    chapters = ChoiceFilter(label='Chapters', choices=CHAPTER_FILTER, method='filter_by_chapters')
    votes = ChoiceFilter(label='Votes', choices=VOTES_FILTER, method='filter_by_votes')
    rating = ChoiceFilter(label='Rating', choices=RATING_FILTER, method='filter_by_rating')

    class Meta:
        model = Book
        fields = ['status_release']

    def __init__(self, *args, **kwargs):
        super(BookFilter, self).__init__(*args, **kwargs)
        self.filters['status_release'].label = 'Completion'

    def filter_by_country(self, qs, name, value):
        if not value == 'all':
            qs = qs if not value else qs.filter(country__iexact=value)
        return qs

    def filter_by_chapters(self, qs, name, value):
        expression = 'chapters_count' if value == 'low' else '-chapters_count'
        return qs.order_by(expression)

    def filter_by_votes(self, qs, name, value):
        expression = 'chapters_count' if value == 'low' else '-chapters_count'
        return qs.order_by(expression)

    def filter_by_rating(self, qs, name, value):
        if not value == 'all':
            qs = qs if not value else qs.filter(rating__gte=value)
        return qs
