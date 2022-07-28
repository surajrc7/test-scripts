from djongo import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import UserManager
from django.db.models import Q
from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _
from social.apps.django_app.default.models import UserSocialAuth
import hashlib
import uuid

# custom Manager class
class CustomUserManager(UserManager):
    def get_by_natural_key(self, username):
        return self.get(
            Q(**{self.model.USERNAME_FIELD: username}) |
            Q(**{self.model.EMAIL_FIELD: username}) 
        )

# Compound classes for models
class Articles(models.Model):
    article_id = models.CharField(max_length=10)
    name = models.CharField(max_length=100)
    tagline = models.TextField()
    domain = models.CharField(max_length=100)

    class Meta:
        abstract = True
        
class Associations(models.Model):
    user_id = models.CharField(max_length=10)
    name = models.CharField(max_length=100)

    class Meta:
        abstract = True


# Create your models here.
GENDER = (('Male','Male '),('Female ','Female '),('Others ','Others '))
OCCUPATION = (('Student', 'Student'),('Employee', 'Employee'),('Researcher', 'Researcher'), ('Others','Others'))

class CustomUser(AbstractUser):
    username_validator = RegexValidator(
        r'^[0-9a-zA-Z]*$', 'Only alphanumeric characters are allowed.')
    username = models.CharField(
        _('username'),
        max_length=150,
        unique=True,
        help_text=_(
            'Required. 150 characters or fewer. Only alphanumeric characters are allowed.'),
        validators=[username_validator],
        error_messages={
            'unique': _("A user with that username already exists."),
        },
    )
    email = models.EmailField(blank=False, unique=True)
    is_email_verified = models.BooleanField(default=False)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    gender = models.CharField(choices=GENDER, default="Male", max_length=7)
    dob = models.DateTimeField(null=True)
    associations = models.EmbeddedField(
        model_container=Associations,null=True, blank=True
    )
    published = models.EmbeddedField(
        model_container=Articles,null=True, blank=True
    )
    location = models.CharField(max_length=100,null=True)
    liked_article = models.EmbeddedField(
        model_container=Articles, null=True, blank=True
    )
    avatar = models.URLField(default='data:image/png;base64,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')
    occupation = models.CharField(choices=OCCUPATION, default="Student", max_length=13)
    headline = models.CharField(max_length=255, null=True, blank=True)
    objects = CustomUserManager()
