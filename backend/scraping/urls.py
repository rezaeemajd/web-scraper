from rest_framework.routers import DefaultRouter
from .views import ScraperViewSet,ScraperRunViewSet
router=DefaultRouter(); router.register("",ScraperViewSet,basename="scraper"); router.register("runs",ScraperRunViewSet,basename="scraper-run")
urlpatterns=router.urls
