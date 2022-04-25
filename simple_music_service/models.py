from django.db import models
from django.contrib.auth.models import User
from django.core.validators import FileExtensionValidator, MinValueValidator, MaxValueValidator
from django_lifecycle import hook, LifecycleModelMixin, AFTER_CREATE, AFTER_UPDATE, AFTER_DELETE
import logging

logger = logging.getLogger("django")


class DatabaseAuditMixin(LifecycleModelMixin):
    def after_event_hook(self):
        for field in self._meta.get_fields():
            if self.has_changed(field.name):
                table = self._meta.db_table
                record_id = self.initial_value("id") if self.id is None else self.id
                column_name = field.name
                old_value = self.initial_value(field.name)
                new_value = getattr(self, field.name)
                DatabaseAudit.objects.create(table=table, record_id=record_id, column_name=column_name,
                                             old_value=old_value, new_value=new_value)

    @hook(AFTER_CREATE)
    def after_create_hook(self):
        self.after_event_hook()
        logger.info(f"after_create_hook for {self}")

    @hook(AFTER_UPDATE)
    def after_update_hook(self):
        self.after_event_hook()
        logger.info(f"after_update_hook for {self}")

    @hook(AFTER_DELETE)
    def after_delete_hook(self):
        self.after_event_hook()
        logger.info(f"after_delete_hook for {self}")


class ApplicationUser(DatabaseAuditMixin, User):
    class Meta:
        proxy = True


class Artist(DatabaseAuditMixin, models.Model):
    name = models.CharField(max_length=50, unique=True)


class Song(DatabaseAuditMixin, models.Model):
    title = models.CharField(max_length=50)
    artist = models.ManyToManyField(Artist)
    year = models.DateField()
    location = models.FileField(
        validators=[FileExtensionValidator(allowed_extensions=["mp3"])]
    )
    user = models.ForeignKey(ApplicationUser, on_delete=models.CASCADE)
    lyrics = models.TextField(null=True)

    @property
    def average_rating(self):
        return self.rating_set.aggregate(models.Avg("mark"))["mark__avg"]

    @property
    def reviews_count(self):
        return self.rating_set.count()

    def delete(self, using=None, keep_parents=False):
        super().delete()
        self.location.delete(save=False)


class Playlist(DatabaseAuditMixin, models.Model):
    title = models.CharField(max_length=50)
    user = models.ForeignKey(ApplicationUser, on_delete=models.CASCADE)
    song = models.ManyToManyField(Song)


class Rating(DatabaseAuditMixin, models.Model):
    song = models.ForeignKey(Song, on_delete=models.CASCADE)
    user = models.ForeignKey(ApplicationUser, on_delete=models.CASCADE)
    mark = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )

    class Meta:
        constraints = [models.UniqueConstraint(fields=["song", "user"], name="unique_song_user_rate")]


class Comment(DatabaseAuditMixin, models.Model):
    song = models.ForeignKey(Song, on_delete=models.CASCADE)
    user = models.ForeignKey(ApplicationUser, null=True, on_delete=models.SET_NULL)
    message = models.CharField(max_length=100)
    created_date_time = models.DateTimeField(auto_now_add=True)


class DatabaseAudit(models.Model):
    created_date_time = models.DateTimeField(auto_now_add=True)
    table = models.CharField(max_length=65)
    record_id = models.BigIntegerField()
    column_name = models.CharField(max_length=65)
    old_value = models.TextField(null=True)
    new_value = models.TextField(null=True)

    class Meta:
        db_table = "simple_music_service_database_audit"
