from django.urls import path, include
from rest_framework_nested import routers
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    SongViewSet,
    ArtistViewSet,
    MyTokenObtainPairView,
    SignupViewSet,
    UserViewSet,
    NestedSongViewSet,
    PlaylistViewSet,
    RatingViewSet
)

router = routers.DefaultRouter()
router.register(r"users", UserViewSet)
router.register(r"songs", SongViewSet)
router.register(r"artists", ArtistViewSet)
router.register(r"signup", SignupViewSet, basename="signup")

users_router = routers.NestedSimpleRouter(router, r"users", lookup="users")
users_router.register(r"songs", NestedSongViewSet, basename="nested-song")
users_router.register(r"playlists", PlaylistViewSet, basename="playlist")

songs_router = routers.NestedSimpleRouter(router, r"songs", lookup="songs")
songs_router.register(r"ratings", RatingViewSet, basename="song-rating")

urlpatterns = [
    path("", include(router.urls)),
    path("", include(users_router.urls)),
    path("", include(songs_router.urls)),
    path("api-auth/", include("rest_framework.urls", namespace="rest_framework")),
    path("token/", MyTokenObtainPairView.as_view(), name="token"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token/refresh"),
]
