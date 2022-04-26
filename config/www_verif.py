from django.conf import settings
from django.views.generic import TemplateView


class GoogleSearchVerif(TemplateView):
    template_name = 'google-verification.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_verif_code'] = settings.WEBMASTER_VERIFICATION["google"]
        return context


class YandexSearchVerif(TemplateView):
    template_name = 'yandex-verification.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_verif_code'] = settings.WEBMASTER_VERIFICATION["yandex"]
        return context
