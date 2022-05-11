from django.db import migrations, models
from functools import partial


def transfer_data(apps, schema_editor, model_name, through_model_name, through_field_name):
    model = apps.get_model('simple_music_service', model_name)
    through_model = apps.get_model('simple_music_service', through_model_name)
    for model_instance in model.objects.all():
        for through_field in getattr(model_instance, through_field_name).all():
            params = {model_name: model_instance, through_field_name: through_field}
            through_model(**params).save()


class Migration(migrations.Migration):
    dependencies = [
        ('simple_music_service', '0012_songplaylist_artistsong'),
    ]

    operations = [
        migrations.RunPython(
            partial(transfer_data, model_name='Song', through_model_name='ArtistSong', through_field_name='artist'),
            reverse_code=migrations.RunPython.noop),

        migrations.RemoveField(
            model_name='song',
            name='artist',
        ),
        migrations.AddField(
            model_name='song',
            name='artist',
            field=models.ManyToManyField(through='simple_music_service.ArtistSong', to='simple_music_service.Artist'),
        ),

        migrations.RunPython(
            partial(transfer_data, model_name='Playlist', through_model_name='SongPlaylist', through_field_name='song'),
            reverse_code=migrations.RunPython.noop),

        migrations.RemoveField(
            model_name='playlist',
            name='song',
        ),
        migrations.AddField(
            model_name='playlist',
            name='song',
            field=models.ManyToManyField(through='simple_music_service.SongPlaylist', to='simple_music_service.Song'),
        ),
    ]
