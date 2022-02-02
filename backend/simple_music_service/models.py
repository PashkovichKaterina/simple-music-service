from django.db import models


class Song(models.Model):
    title = models.CharField(max_length=50)
    artist = models.CharField(max_length=50)
    year = models.DateField()
    location = models.CharField(max_length=100)
