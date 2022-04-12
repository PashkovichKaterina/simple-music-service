from django.db import models
from django.contrib.auth.models import User
from django.core.validators import FileExtensionValidator, MinValueValidator, MaxValueValidator


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

    @property
    def average_rating(self):
        return self.rating_set.aggregate(models.Avg("mark"))["mark__avg"]

    @property
    def reviews_count(self):
        return self.rating_set.count()

    def delete(self, using=None, keep_parents=False):
        super().delete()
        self.location.delete(save=False)


class Playlist(models.Model):
    title = models.CharField(max_length=50)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    song = models.ManyToManyField(Song)


class Rating(models.Model):
    song = models.ForeignKey(Song, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    mark = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )

    class Meta:
        constraints = [models.UniqueConstraint(fields=["song", "user"], name="unique_song_user_rate")]


class Comment(models.Model):
    song = models.ForeignKey(Song, on_delete=models.CASCADE)
    user = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    message = models.CharField(max_length=100)
    created_date_time = models.DateTimeField(auto_now_add=True)
