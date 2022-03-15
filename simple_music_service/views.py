from rest_framework import viewsets
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.response import Response
from rest_framework.filters import SearchFilter
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from .serializers import (
    SongSerializer,
    ArtistSerializer,
    MyTokenObtainPairSerializer,
    UserSerializer,
    PlaylistSerializer
)
from .models import Song, Artist, Playlist
from .permissions import IsOwner


class SongViewSet(viewsets.ModelViewSet):
    queryset = Song.objects.all()
    serializer_class = SongSerializer
    http_method_names = ["get"]
    filter_backends = [SearchFilter]
    search_fields = ["title", "artist__name"]


class NestedSongViewSet(SongViewSet):
    http_method_names = ["get", "post", "delete"]

    def get_queryset(self):
        return Song.objects.filter(user=self.kwargs["users_pk"])

    def retrieve(self, request, pk=None, users_pk=None):
        item = get_object_or_404(self.queryset, pk=pk, user=users_pk)
        serializer = self.get_serializer(item)
        return Response(serializer.data)


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
    filter_backends = [SearchFilter]
    search_fields = ["^title"]

    def get_queryset(self):
        return Playlist.objects.filter(user=self.kwargs["users_pk"])

    def retrieve(self, request, pk=None, users_pk=None):
        item = get_object_or_404(self.queryset, pk=pk, user=users_pk)
        serializer = self.get_serializer(item)
        return Response(serializer.data)
