from django.urls import path, include
from rest_framework import routers
from .views import SongViewSet, ArtistViewSet

router = routers.DefaultRouter()
router.register(r"songs", SongViewSet)
router.register(r"artists", ArtistViewSet)

urlpatterns = [
    path("", include(router.urls)),
    path("api-auth/", include("rest_framework.urls", namespace="rest_framework")),
]
