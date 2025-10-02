# jobs/urls.py
from rest_framework.routers import DefaultRouter
from .views import VacanteViewSet

router = DefaultRouter()
router.register(r"jobs", VacanteViewSet, basename="jobs")

urlpatterns = router.urls

