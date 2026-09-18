from rest_framework.routers import DefaultRouter
from .views import ExtractedRecordViewSet
router=DefaultRouter(); router.register("records",ExtractedRecordViewSet,basename="record")
urlpatterns=router.urls
