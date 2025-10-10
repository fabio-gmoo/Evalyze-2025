# jobs/urls.py
from rest_framework.routers import SimpleRouter  # type: ignore
from .views import VacanteViewSet

router = SimpleRouter()  # Usamos SimpleRouter para tener más control
router.register(r"jobs", VacanteViewSet, basename="jobs")

urlpatterns = router.urls
