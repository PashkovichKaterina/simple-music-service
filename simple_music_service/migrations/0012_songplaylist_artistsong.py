from django.db import migrations, models
import django.db.models.deletion
import simple_music_service.models


class Migration(migrations.Migration):
    dependencies = [
        ('simple_music_service', '0011_artist_deleted_date_time_comment_deleted_date_time_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='SongPlaylist',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('deleted_date_time', models.DateTimeField(default=None, null=True)),
                ('playlist',
                 models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='simple_music_service.playlist')),
                (
                    'song',
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='simple_music_service.song')),
            ],
            options={
                'db_table': 'simple_music_service_song_playlist',
            },
            bases=(simple_music_service.models.DatabaseAuditMixin, models.Model),
        ),
        migrations.CreateModel(
            name='ArtistSong',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('deleted_date_time', models.DateTimeField(default=None, null=True)),
                ('artist',
                 models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='simple_music_service.artist')),
                (
                    'song',
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='simple_music_service.song')),
            ],
            options={
                'db_table': 'simple_music_service_artist_song',
            },
            bases=(simple_music_service.models.DatabaseAuditMixin, models.Model),
        ),
    ]
