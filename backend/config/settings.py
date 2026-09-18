import os
from pathlib import Path
BASE_DIR=Path(__file__).resolve().parent.parent
SECRET_KEY=os.getenv("DJANGO_SECRET_KEY","unsafe-dev-key")
DEBUG=os.getenv("DEBUG","False").lower()=="true"
ALLOWED_HOSTS=[x for x in os.getenv("ALLOWED_HOSTS","localhost,127.0.0.1").split(",") if x]
INSTALLED_APPS=["django.contrib.admin","django.contrib.auth","django.contrib.contenttypes","django.contrib.sessions","django.contrib.messages","django.contrib.staticfiles","corsheaders","rest_framework","drf_spectacular","core","sources","scraping","datahub","exports"]
MIDDLEWARE=["django.middleware.security.SecurityMiddleware","corsheaders.middleware.CorsMiddleware","django.contrib.sessions.middleware.SessionMiddleware","django.middleware.common.CommonMiddleware","django.middleware.csrf.CsrfViewMiddleware","django.contrib.auth.middleware.AuthenticationMiddleware","django.contrib.messages.middleware.MessageMiddleware","django.middleware.clickjacking.XFrameOptionsMiddleware"]
ROOT_URLCONF="config.urls"
TEMPLATES=[{"BACKEND":"django.template.backends.django.DjangoTemplates","DIRS":[],"APP_DIRS":True,"OPTIONS":{"context_processors":["django.template.context_processors.request","django.contrib.auth.context_processors.auth","django.contrib.messages.context_processors.messages"]}}]
WSGI_APPLICATION="config.wsgi.application"
DATABASES={"default":{"ENGINE":"django.db.backends.postgresql","NAME":os.getenv("POSTGRES_DB","cdi"),"USER":os.getenv("POSTGRES_USER","cdi"),"PASSWORD":os.getenv("POSTGRES_PASSWORD","change-me"),"HOST":os.getenv("POSTGRES_HOST","db"),"PORT":os.getenv("POSTGRES_PORT","5432")}}
LANGUAGE_CODE="fa-ir"; TIME_ZONE="Asia/Tehran"; USE_I18N=True; USE_TZ=True
STATIC_URL="/static/"; STATIC_ROOT=BASE_DIR/"staticfiles"
DEFAULT_AUTO_FIELD="django.db.models.BigAutoField"
CORS_ALLOWED_ORIGINS=[x for x in os.getenv("CORS_ALLOWED_ORIGINS","http://localhost:3001").split(",") if x]
REST_FRAMEWORK={"DEFAULT_SCHEMA_CLASS":"drf_spectacular.openapi.AutoSchema","DEFAULT_AUTHENTICATION_CLASSES":["rest_framework.authentication.SessionAuthentication","rest_framework.authentication.BasicAuthentication"],"DEFAULT_PERMISSION_CLASSES":["rest_framework.permissions.IsAuthenticatedOrReadOnly"],"DEFAULT_FILTER_BACKENDS":["django_filters.rest_framework.DjangoFilterBackend","rest_framework.filters.SearchFilter","rest_framework.filters.OrderingFilter"]}
SPECTACULAR_SETTINGS={"TITLE":"Cofinets Data Intelligence API","VERSION":"1.0.0","SERVE_INCLUDE_SCHEMA":False}
CELERY_BROKER_URL=os.getenv("CELERY_BROKER_URL","redis://redis:6379/0"); CELERY_RESULT_BACKEND=os.getenv("CELERY_RESULT_BACKEND","redis://redis:6379/1")
