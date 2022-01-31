from rest_framework import generics
from . import serializers
from .models import Song


class SongListView(generics.ListAPIView):
    queryset = Song.objects.all()
    serializer_class = serializers.SongSerializer


class SongDetailView(generics.RetrieveAPIView):
    queryset = Song.objects.all()
    serializer_class = serializers.SongSerializer
