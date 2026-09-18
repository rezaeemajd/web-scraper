from rest_framework.routers import DefaultRouter
from .views import EntityTypeViewSet,EntityFieldViewSet,LocationViewSet,RawCaptureViewSet,ExtractedRecordViewSet,DedupCandidateViewSet,ReviewTaskViewSet,AuditEventViewSet
router=DefaultRouter()
router.register("entity-types",EntityTypeViewSet,basename="entity-type"); router.register("fields",EntityFieldViewSet,basename="entity-field"); router.register("locations",LocationViewSet,basename="location"); router.register("raw",RawCaptureViewSet,basename="raw-capture"); router.register("records",ExtractedRecordViewSet,basename="record"); router.register("duplicates",DedupCandidateViewSet,basename="duplicate"); router.register("reviews",ReviewTaskViewSet,basename="review"); router.register("audit",AuditEventViewSet,basename="audit")
urlpatterns=router.urls
