"""aimamaproject URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.contrib.auth.views import LogoutView
from userapp import views as views_main
from django.conf.urls import url
from rest_framework_swagger.views import get_swagger_view

from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi



schema_view = get_schema_view(
    openapi.Info(
        title="AIMama Project API",
        default_version='v1',
        description="Welcome to the world of Jaseci",
        terms_of_service="https://www.jaseci.org",
        contact=openapi.Contact(email="vivekmurali00@outlook.com"),
        license=openapi.License(name="Awesome IP"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)


urlpatterns = [
    path('admin/', admin.site.urls, name='admin'),
    re_path(r'^doc(?P<format>\.json|\.yaml)$',schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('', include('social_django.urls', namespace='social')),
    path('', views_main.index, name='home'),
    path('logout/',LogoutView.as_view(template_name=settings.LOGOUT_REDIRECT_URL),name='logout'),
    path('doc/', schema_view.with_ui('swagger', cache_timeout=0),name='schema-swagger-ui'),  #<-- Here
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0),name='schema-redoc'),  #<-- Here  # <-- Here
    path('aiapiv1/', include('ai.urls')),
    path('ui/', include('django.contrib.auth.urls')),
    path('auth/', include('userapp.urls')),
]

handler404 = "helpers.views.handle_not_found"
handler500 = "helpers.views.handle_server_error"