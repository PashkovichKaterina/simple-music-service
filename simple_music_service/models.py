from django.db import models


class Artist(models.Model):
    name = models.CharField(max_length=50)


class Song(models.Model):
    title = models.CharField(max_length=50)
    artist = models.ManyToManyField(Artist)
    year = models.DateField()
    location = models.CharField(max_length=100)
