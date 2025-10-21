from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class GuestsConfig(AppConfig):
    default_auto_field = 'django.db.models.AutoField'
    name = 'guests'
    verbose_name = _('Convidados')
