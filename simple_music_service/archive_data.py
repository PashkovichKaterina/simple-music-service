from csv import DictWriter
from zipfile import ZipFile
from io import BytesIO, StringIO
import requests
from .models import ApplicationUser, Song, Playlist, Rating, Comment
from functools import reduce
import logging

logger = logging.getLogger("django")


def get_archive_with_user_data(user_id):
    with BytesIO() as memory:
        with ZipFile(memory, "w") as zip_file:
            save_uploaded_songs(zip_file, user_id)
            zip_file.writestr("personal_data.csv", get_personal_data_file(user_id))
            zip_file.writestr("uploaded_songs.csv", get_uploaded_songs_file(user_id))
            zip_file.writestr("created_playlists.csv", get_created_playlists_file(user_id))
            zip_file.writestr("ratings.csv", get_ratings_file(user_id))
            zip_file.writestr("comments.csv", get_comments_file(user_id))
        return memory.getvalue()


def save_uploaded_songs(zip_file, user_id):
    uploaded_songs = Song.objects.filter(user=user_id)
    for song in uploaded_songs:
        artist = get_artist_name(song.artist)
        try:
            response = requests.get(song.location.url)
            if response.status_code == 200:
                with BytesIO(response.content) as file:
                    zip_file.writestr(f"uploaded_song/{song.title} - {artist}.mp3", file.getvalue())
            else:
                logger.info(f"Response code {response.status_code} for getting file {song.location.url}")
        except requests.exceptions.RequestException as exception:
            logger.info(f"Exception occurred while downloading song {song.title} - {artist}: {exception}")


def get_csv_file(header, data):
    with StringIO() as csv_file:
        writer = DictWriter(csv_file, fieldnames=header)
        writer.writeheader()
        writer.writerows(data)
        return csv_file.getvalue()


def get_personal_data_file(user_id):
    file_header = ["identifier", "username", "email"]
    user = ApplicationUser.objects.get(id=user_id)
    file_data = [{"identifier": user.id, "username": user.username, "email": user.email}]
    return get_csv_file(file_header, file_data)


def get_created_playlists_file(user_id):
    file_header = ["identifier", "title", "song_title", "song_artist"]
    created_playlists = Playlist.objects.filter(user=user_id)
    file_data = []
    for playlist in created_playlists:
        for song in playlist.song.all():
            playlist_dict = {"identifier": playlist.id, "title": playlist.title, "song_title": song.title,
                             "song_artist": get_artist_name(song.artist)}
            file_data.append(playlist_dict)
    return get_csv_file(file_header, file_data)


def get_uploaded_songs_file(user_id):
    instance_fields = {"identifier": "id", "title": "title", "artist": "artist", "release_date": "year"}
    return get_file_data(Song, instance_fields, user_id)


def get_ratings_file(user_id):
    instance_fields = {"song_title": "song.title", "song_artist": "song.artist", "mark": "mark"}
    return get_file_data(Rating, instance_fields, user_id)


def get_comments_file(user_id):
    instance_fields = {"song_title": "song.title", "song_artist": "song.artist", "comment": "message"}
    return get_file_data(Comment, instance_fields, user_id)


def get_file_data(model, instance_fields, user_id):
    file_header = instance_fields.keys()
    instances = model.objects.filter(user=user_id)
    file_data = []
    for instance in instances:
        instance_dict = {}
        for column_head, instance_filed in instance_fields.items():
            field_value = reduce(getattr, instance_filed.split("."), instance)
            if "artist" in instance_filed:
                field_value = get_artist_name(field_value)
            instance_dict.update({column_head: field_value})
        file_data.append(instance_dict)
    return get_csv_file(file_header, file_data)


def get_artist_name(artists):
    artist_names = [artist.name for artist in artists.all()]
    return ", ".join(artist_names)
