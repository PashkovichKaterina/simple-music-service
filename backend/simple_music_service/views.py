from rest_framework import viewsets
from . import serializers
from .models import Song


class SongViewSet(viewsets.ModelViewSet):
    queryset = Song.objects.all()
    serializer_class = serializers.SongSerializer
