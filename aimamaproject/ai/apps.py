from django.apps import AppConfig
from .src.main import Associations


class AiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'ai'
    Associations = Associations()