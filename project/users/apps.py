from django.apps import AppConfig
from .src.main import (Associations, Citations)


class UsersConfig(AppConfig):
    name = 'users'
    Associations = Associations()
    Citations = Citations()
