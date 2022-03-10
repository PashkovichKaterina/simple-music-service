from django.db import models
from django.contrib.auth.models import User
from django.core.validators import FileExtensionValidator


class Artist(models.Model):
    name = models.CharField(max_length=50, unique=True)


class Song(models.Model):
    title = models.CharField(max_length=50)
    artist = models.ManyToManyField(Artist)
    year = models.DateField()
    location = models.FileField(
        validators=[FileExtensionValidator(allowed_extensions=["mp3"])]
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)


class Playlist(models.Model):
    title = models.CharField(max_length=50)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    song = models.ManyToManyField(Song)
