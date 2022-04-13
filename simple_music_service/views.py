from rest_framework import viewsets, status
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.response import Response
from rest_framework.filters import SearchFilter, OrderingFilter
from django.shortcuts import get_object_or_404
from django.db.models import Avg
from django.contrib.auth.models import User
from .serializers import (
    SongSerializer,
    ArtistSerializer,
    MyTokenObtainPairSerializer,
    UserSerializer,
    PlaylistSerializer,
    RatingSerializer,
    CommentForSongSerializer,
    CommentForUserSerializer
)
from .models import Song, Artist, Playlist, Rating, Comment
from .permissions import IsOwner
from .paginations import PageNumberAndPageSizePagination
from .filters import NotNoneValuesLargerOrderingFilter
from .feature_flags import get_feature_flag_value


class SongViewSet(viewsets.ModelViewSet):
    queryset = Song.objects.annotate(avg_rating=Avg("rating__mark")).all()
    serializer_class = SongSerializer
    http_method_names = ["get"]
    filter_backends = [SearchFilter, NotNoneValuesLargerOrderingFilter]
    pagination_class = PageNumberAndPageSizePagination
    search_fields = ["title", "artist__name"]
    ordering_fields = ["title", "year", "avg_rating"]
    ordering = ["-year"]


class NestedSongViewSet(SongViewSet):
    http_method_names = ["get", "post", "delete"]
    permission_classes = (IsOwner,)

    def get_queryset(self):
        return Song.objects.annotate(avg_rating=Avg("rating__mark")).filter(user=self.kwargs["users_pk"])

    def retrieve(self, request, pk=None, users_pk=None):
        item = get_object_or_404(self.queryset, pk=pk, user=users_pk)
        serializer = self.get_serializer(item)
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        is_delete_song_available = get_feature_flag_value("isDeleteSongAvailable")
        if is_delete_song_available:
            super().destroy(request, *args, **kwargs)
        else:
            response = {"detail": "Method \"DELETE\" not allowed."}
            return Response(response, status=status.HTTP_405_METHOD_NOT_ALLOWED)


class ArtistViewSet(viewsets.ModelViewSet):
    queryset = Artist.objects.all()
    serializer_class = ArtistSerializer


class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer


class SignupViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    http_method_names = ["post"]
    permission_classes = (AllowAny,)


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    http_method_names = []


class PlaylistViewSet(viewsets.ModelViewSet):
    queryset = Playlist.objects.all()
    serializer_class = PlaylistSerializer
    permission_classes = (IsOwner,)
    filter_backends = [SearchFilter, OrderingFilter]
    pagination_class = PageNumberAndPageSizePagination
    search_fields = ["^title"]
    ordering_fields = ["title"]
    ordering = ["title"]

    def get_queryset(self):
        return Playlist.objects.filter(user=self.kwargs["users_pk"])

    def retrieve(self, request, pk=None, users_pk=None):
        item = get_object_or_404(self.queryset, pk=pk, user=users_pk)
        serializer = self.get_serializer(item)
        return Response(serializer.data)


class RatingViewSet(viewsets.ModelViewSet):
    serializer_class = RatingSerializer
    http_method_names = ["post", "patch"]

    def get_queryset(self):
        return Rating.objects.filter(song=self.kwargs["songs_pk"])


class CommentForSongViewSet(viewsets.ModelViewSet):
    serializer_class = CommentForSongSerializer
    pagination_class = PageNumberAndPageSizePagination
    filter_backends = [OrderingFilter]
    ordering_fields = ["created_date_time"]
    ordering = ["created_date_time"]

    def get_queryset(self):
        return Comment.objects.filter(song=self.kwargs["songs_pk"])


class CommentForUserViewSet(viewsets.ModelViewSet):
    serializer_class = CommentForUserSerializer
    http_method_names = ["get", "patch", "delete"]
    permission_classes = (IsOwner,)
    pagination_class = PageNumberAndPageSizePagination
    filter_backends = [OrderingFilter]
    ordering_fields = ["created_date_time"]
    ordering = ["created_date_time"]

    def get_queryset(self):
        return Comment.objects.filter(user=self.kwargs["users_pk"])
