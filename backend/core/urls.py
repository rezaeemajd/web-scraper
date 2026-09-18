from django.urls import path
from .views import health,ready
urlpatterns=[path("health/",health),path("ready/",ready)]
