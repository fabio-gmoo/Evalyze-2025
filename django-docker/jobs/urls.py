# jobs/urls.py
from rest_framework.routers import SimpleRouter  # type: ignore
from .views import VacanteViewSet
from .views_interview import InterviewSessionViewSet  # type: ignore

router = SimpleRouter()  # Usamos SimpleRouter para tener más control
router.register(r"jobs", VacanteViewSet, basename="jobs")
# fmt: off
router.register(r"interview-sessions", InterviewSessionViewSet, basename="interview-sessions")
# fmt: on
urlpatterns = router.urls
