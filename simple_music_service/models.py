from django.db import models
from django.contrib.auth.models import User
from django.core.validators import FileExtensionValidator, MinValueValidator, MaxValueValidator
from django_lifecycle import hook, LifecycleModelMixin, AFTER_CREATE, AFTER_UPDATE, BEFORE_DELETE
import logging
import datetime
from .managers import SoftDeleteManager

logger = logging.getLogger("django")


class DatabaseAuditMixin(LifecycleModelMixin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._initial_m2m_values = {}

    @hook(AFTER_CREATE)
    def _after_create_hook(self):
        logger.info(f"after_create_hook for {self}")

        def handle_m2m_field(field):
            self._initial_m2m_values.update({field.column: set()})

        def save_field_changes(field):
            self._save_audit_data(instance=self, field=field, new_value=getattr(self, field.column))

        self._event_hook(handle_m2m_field, save_field_changes)

    @hook(AFTER_UPDATE)
    def _after_update_hook(self):
        logger.info(f"after_update_hook for {self}")

        def handle_m2m_field(field):
            key = field.name
            filter_parameters = {field.remote_field.name: self.id}
            if not self._initial_m2m_values:
                through_instances = set(getattr(field.model, field.name).through.objects.filter(**filter_parameters))
                self._initial_m2m_values.update({key: through_instances})
            else:
                before_instances = self._initial_m2m_values[key]
                after_instances = set(getattr(field.model, field.name).through.objects.filter(**filter_parameters))
                if before_instances != after_instances:
                    deleted_instances = before_instances.difference(after_instances)
                    added_instances = after_instances.difference(before_instances)
                    for instance in deleted_instances:
                        for instance_field in instance._meta.get_fields():
                            self._save_audit_data(instance=instance, field=instance_field,
                                                  old_value=getattr(instance, instance_field.column))
                    for instance in added_instances:
                        for instance_field in instance._meta.get_fields():
                            self._save_audit_data(instance=instance, field=instance_field,
                                                  new_value=getattr(instance, instance_field.column))

        def save_field_changes(field):
            if self.has_changed(field.name):
                self._save_audit_data(instance=self, field=field, old_value=self.initial_value(field.column),
                                      new_value=getattr(self, field.column))

        self._event_hook(handle_m2m_field, save_field_changes)

    @hook(BEFORE_DELETE)
    def _before_delete_hook(self):
        logger.info(f"before_delete_hook for {self}")

        def handle_m2m_field(field):
            filter_parameters = {field.remote_field.name: self.id}
            through_instances = getattr(field.model, field.name).through.objects.filter(**filter_parameters)
            for through in through_instances:
                for through_field in through._meta.get_fields():
                    self._save_audit_data(instance=through, field=through_field,
                                          old_value=getattr(through, through_field.column))

        def save_field_changes(field):
            self._save_audit_data(instance=self, field=field, old_value=self.initial_value(field.column))

        self._event_hook(handle_m2m_field, save_field_changes)

    def _event_hook(self, handle_m2m_field, save_field_changes):
        for field in self._meta.get_fields():
            if not isinstance(field, models.ManyToOneRel) and not isinstance(field, models.ManyToManyRel):
                if isinstance(field, models.ManyToManyField):
                    handle_m2m_field(field)
                else:
                    save_field_changes(field)

    @staticmethod
    def _save_audit_data(*, instance, field, old_value=None, new_value=None):
        table = instance._meta.db_table
        record_id = instance.id
        column_name = field.column
        DatabaseAudit.objects.create(table=table, record_id=record_id, column_name=column_name,
                                     old_value=old_value, new_value=new_value)


class SoftDeleteModel(models.Model):
    deleted_date_time = models.DateTimeField(null=True, default=None)
    objects = SoftDeleteManager()
    all_objects = models.Manager()

    def delete(self, using=None, keep_parents=False):
        logger.info(f"Delete object {self}")
        self.deleted_date_time = datetime.datetime.now()
        self.save()

    class Meta:
        abstract = True


class ApplicationUser(DatabaseAuditMixin, User):
    class Meta:
        proxy = True


class Artist(DatabaseAuditMixin, SoftDeleteModel):
    name = models.CharField(max_length=50, unique=True)


class Song(DatabaseAuditMixin, SoftDeleteModel):
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


class Playlist(DatabaseAuditMixin, SoftDeleteModel):
    title = models.CharField(max_length=50)
    user = models.ForeignKey(ApplicationUser, on_delete=models.CASCADE)
    song = models.ManyToManyField(Song)


class Rating(DatabaseAuditMixin, SoftDeleteModel):
    song = models.ForeignKey(Song, on_delete=models.CASCADE)
    user = models.ForeignKey(ApplicationUser, on_delete=models.CASCADE)
    mark = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )

    class Meta:
        constraints = [models.UniqueConstraint(fields=["song", "user"], name="unique_song_user_rate")]


class Comment(DatabaseAuditMixin, SoftDeleteModel):
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
