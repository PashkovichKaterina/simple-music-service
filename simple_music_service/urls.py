from django.urls import path, include
from rest_framework import routers
from rest_framework_simplejwt.views import TokenRefreshView
from .views import SongViewSet, ArtistViewSet, MyTokenObtainPairView, SignupViewSet

router = routers.DefaultRouter()
router.register(r"songs", SongViewSet)
router.register(r"artists", ArtistViewSet)
router.register(r"signup", SignupViewSet)

urlpatterns = [
    path("", include(router.urls)),
    path("api-auth/", include("rest_framework.urls", namespace="rest_framework")),
    path("token/", MyTokenObtainPairView.as_view()),
    path("token/refresh/", TokenRefreshView.as_view()),
]
