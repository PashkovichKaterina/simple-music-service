from csv import DictWriter
from zipfile import ZipFile
from io import BytesIO, StringIO
import requests
from .models import ApplicationUser, Song, Playlist, Rating, Comment, DatabaseAudit
from functools import reduce
import logging

logger = logging.getLogger("django")


def get_archive_with_user_data(user_id, from_date, to_date):
    with BytesIO() as memory:
        with ZipFile(memory, "w") as zip_file:
            save_uploaded_songs(zip_file, user_id)
            zip_file.writestr("personal_data.csv", get_personal_data_file(user_id))
            zip_file.writestr("uploaded_songs.csv", get_uploaded_songs_file(user_id))
            zip_file.writestr("created_playlists.csv", get_created_playlists_file(user_id))
            zip_file.writestr("ratings.csv", get_ratings_file(user_id))
            zip_file.writestr("comments.csv", get_comments_file(user_id))
            zip_file.writestr("event_history.csv", get_event_history_file(user_id, from_date, to_date))
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
        if playlist.song.exists():
            for song in playlist.song.all():
                file_data.append({"identifier": playlist.id, "title": playlist.title, "song_title": song.title,
                                  "song_artist": get_artist_name(song.artist)})
        else:
            file_data.append({"identifier": playlist.id, "title": playlist.title, "song_title": "",
                              "song_artist": ""})
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


def get_event_history_file(user_id, from_date, to_date):
    file_header = ["event_date_time", "description"]
    file_data = get_signup_data(user_id, from_date, to_date)
    file_data.extend(get_song_event_history(user_id, from_date, to_date))
    file_data.extend(get_playlist_event_history(user_id, from_date, to_date))
    file_data.extend(get_rating_event_history(user_id, from_date, to_date))
    file_data.extend(get_comment_event_history(user_id, from_date, to_date))
    file_data = sorted(file_data, key=lambda data: data["event_date_time"])
    return get_csv_file(file_header, file_data)


def get_signup_data(user_id, from_date, to_date):
    filter_params = {"table": "auth_user", "record_id": user_id, "column_name": "id", "old_value": None}
    add_date_params_to_filter(filter_params, from_date, to_date)
    signup_info = DatabaseAudit.objects.filter(**filter_params)
    data = []
    if signup_info.exists():
        data.append({"event_date_time": signup_info.first().created_date_time, "description": "Signed up"})
    return data


def get_song_event_history(user_id, from_date, to_date):
    def get_songs_data(*, is_uploaded):
        column_name1 = "new_value" if is_uploaded else "old_value"
        column_name2 = "old_value" if is_uploaded else "new_value"
        description = "Uploaded song '{title} - {artist}'" if is_uploaded else "Deleted song '{title} - {artist}'"
        get_songs_query = f"""
        SELECT audit.id, audit.created_date_time, song_title.{column_name1} as song_title,
            (SELECT ARRAY_AGG(name)
                FROM simple_music_service_artist
                    INNER JOIN simple_music_service_database_audit as artist_id
                        ON simple_music_service_artist.id = artist_id.new_value::integer
                    INNER JOIN simple_music_service_database_audit as through_song_id
                        ON artist_id.record_id = through_song_id.record_id
                WHERE artist_id."table" = 'simple_music_service_song_artist'
                    and artist_id.old_value is NULL and artist_id.column_name = 'artist_id'
                    and through_song_id."table" = 'simple_music_service_song_artist'
                    and through_song_id.{column_name2} is NULL and through_song_id.column_name = 'song_id'
                    and through_song_id.{column_name1} = song_id.{column_name1}) as song_artist
        FROM simple_music_service_database_audit as audit
            INNER JOIN simple_music_service_database_audit as song_id
                ON audit.record_id = song_id.record_id
            INNER JOIN simple_music_service_database_audit as song_title
                ON song_id.record_id = song_title.record_id
        WHERE audit."table" = 'simple_music_service_song' and audit.column_name = 'user_id'
            and song_id."table" = 'simple_music_service_song' and song_id.column_name = 'id'
            and song_id.{column_name2} is NULL and song_title."table" = 'simple_music_service_song'
            and song_title.column_name = 'title' and song_title.{column_name2} is NULL
            and audit.{column_name1} = %(user_id)s
        """
        query_params = {"user_id": user_id}
        get_songs_query, query_params = form_query_and_params_with_date(get_songs_query, query_params,
                                                                        from_date, to_date)
        data = []
        songs = DatabaseAudit.objects.raw(get_songs_query, query_params)
        for song in songs:
            data.append(
                {"event_date_time": song.created_date_time,
                 "description": description.format(title=song.song_title, artist=", ".join(song.song_artist))})
        return data

    uploaded_song = get_songs_data(is_uploaded=True)
    deleted_song = get_songs_data(is_uploaded=False)
    return uploaded_song + deleted_song


def get_playlist_event_history(user_id, from_date, to_date):
    def get_playlist_songs(*, is_added, playlist_id, playlist_title):
        column_name = "new_value" if is_added else "old_value"
        description = "Added song '{song_title} - {song_artist}' to playlist '{playlist_title}'" if is_added \
            else "Deleted song '{song_title} - {song_artist}' from playlist '{playlist_title}'"
        get_playlist_song_query = f"""
        SELECT audit.id, audit.created_date_time, song_title.new_value as song_title,
            (SELECT ARRAY_AGG((SELECT name
                                    FROM simple_music_service_artist
                                        INNER JOIN simple_music_service_database_audit as audit
                                            ON simple_music_service_artist.id = audit.new_value::integer
                                    WHERE "table" = 'simple_music_service_song_artist' and old_value is NULL 
                                    and column_name = 'artist_id' and record_id = song_artist_id.record_id))
            FROM simple_music_service_database_audit as song_artist_id
            WHERE "table" = 'simple_music_service_song_artist' and old_value is NULL 
                and column_name = 'song_id' and new_value = song_id.new_value) as song_artist
        FROM simple_music_service_database_audit as audit
            INNER JOIN simple_music_service_database_audit as song_id
                ON audit.record_id = song_id.record_id
            INNER JOIN simple_music_service_database_audit as song_title
                ON song_id.new_value::integer = song_title.record_id
        WHERE song_id."table" = 'simple_music_service_playlist_song' and song_id.column_name = 'song_id'
            and song_title."table" = 'simple_music_service_song' and song_title.column_name = 'title'
            and song_title.old_value is NULL and audit."table" = 'simple_music_service_playlist_song'
            and audit.column_name = 'playlist_id' and audit.{column_name} = %(playlist_id)s
        """
        query_params = {"playlist_id": playlist_id}
        get_playlist_song_query, query_params = form_query_and_params_with_date(get_playlist_song_query, query_params,
                                                                                from_date, to_date)
        data = []
        songs = DatabaseAudit.objects.raw(get_playlist_song_query, query_params)
        for song in songs:
            data.append(
                {"event_date_time": song.created_date_time,
                 "description": description.format(song_title=song.song_title, song_artist=", ".join(song.song_artist),
                                                   playlist_title=playlist_title)})
        return data

    def get_playlists_data(*, is_created):
        column_name1 = "new_value" if is_created else "old_value"
        column_name2 = "old_value" if is_created else "new_value"
        description = "Created playlist '{title}'" if is_created else "Deleted playlist '{title}'"
        get_playlists_query = f"""
        SELECT audit.id, audit.created_date_time, playlist_id.{column_name1} as playlist_id, 
                playlist_title.{column_name1} as playlist_title
            FROM simple_music_service_database_audit as audit
                INNER JOIN simple_music_service_database_audit as playlist_title
                    ON audit.record_id = playlist_title.record_id
                INNER JOIN simple_music_service_database_audit as playlist_id
                    ON audit.record_id = playlist_id.record_id
        WHERE audit."table" = 'simple_music_service_playlist' and audit.column_name = 'user_id'
            and playlist_title."table" = 'simple_music_service_playlist' and playlist_title.column_name = 'title'
            and playlist_title.{column_name2} is NULL and playlist_id."table" = 'simple_music_service_playlist'
            and playlist_id.column_name = 'id' and playlist_id.{column_name2} is NULL 
            and audit.{column_name1} = %(user_id)s
            """
        query_params = {"user_id": user_id}
        get_playlists_query, query_params = form_query_and_params_with_date(get_playlists_query, query_params,
                                                                            from_date, to_date)
        data = []
        playlists = DatabaseAudit.objects.raw(get_playlists_query, query_params)
        for playlist in playlists:
            added_song = get_playlist_songs(is_added=True, playlist_id=playlist.playlist_id,
                                            playlist_title=playlist.playlist_title)
            deleted_song = get_playlist_songs(is_added=False, playlist_id=playlist.playlist_id,
                                              playlist_title=playlist.playlist_title)
            data.extend(added_song + deleted_song)
            data.append(
                {"event_date_time": playlist.created_date_time,
                 "description": description.format(title=playlist.playlist_title)})
        return data

    created_playlist = get_playlists_data(is_created=True)
    deleted_playlist = get_playlists_data(is_created=False)
    return created_playlist + deleted_playlist


def get_rating_event_history(user_id, from_date, to_date):
    get_ratings_query = """
    SELECT DISTINCT audit.record_id as id, song_title.new_value as song_title,
        (SELECT ARRAY_AGG(name)
            FROM simple_music_service_artist
                INNER JOIN simple_music_service_database_audit as artist_id
                    ON simple_music_service_artist.id = artist_id.new_value::integer
                INNER JOIN simple_music_service_database_audit as song_artist_id
                    ON artist_id.record_id = song_artist_id.record_id
            WHERE artist_id."table" = 'simple_music_service_song_artist' and artist_id.old_value is NULL
                and artist_id.column_name = 'artist_id' and song_artist_id."table" = 'simple_music_service_song_artist'
                and song_artist_id.old_value is NULL and song_artist_id.column_name = 'song_id'
                and song_artist_id.new_value = song_id.new_value) as song_artist
    FROM simple_music_service_database_audit as audit
        INNER JOIN simple_music_service_database_audit as song_id
            ON audit.record_id = song_id.record_id
        INNER JOIN simple_music_service_database_audit as song_title
            ON song_id.new_value::integer = song_title.record_id
    WHERE audit."table" = 'simple_music_service_rating' and audit.column_name = 'user_id'
        and song_id."table" = 'simple_music_service_rating' and song_id.column_name = 'song_id'
        and song_id.new_value is NOT NULL and song_title."table" = 'simple_music_service_song'
        and song_title.column_name = 'title' and song_title.new_value is NOT NULL and audit.new_value = %(user_id)s
    """
    query_params = {"user_id": user_id}
    get_ratings_query, query_params = form_query_and_params_with_date(get_ratings_query, query_params,
                                                                      from_date, to_date)
    data = []
    ratings = DatabaseAudit.objects.raw(get_ratings_query, query_params)
    for rating in ratings:
        filter_params = {"table": "simple_music_service_rating", "record_id": rating.id, "column_name": "mark"}
        add_date_params_to_filter(filter_params, from_date, to_date)
        marks = DatabaseAudit.objects.filter(**filter_params)
        for mark in marks:
            if mark.old_value is None:
                description = "Rated song '{song_title} - {song_artist}' with a rating {new_value}"
            else:
                description = "Changed rating for song '{song_title} - {song_artist}' from {old_value} to {new_value}"
            data.append({"event_date_time": mark.created_date_time,
                         "description": description.format(song_title=rating.song_title,
                                                           song_artist=", ".join(rating.song_artist),
                                                           new_value=mark.new_value, old_value=mark.old_value)})
    return data


def get_comment_event_history(user_id, from_date, to_date):
    get_comments_query = """
    SELECT DISTINCT audit.record_id as id, song_title.new_value as song_title,
        (SELECT ARRAY_AGG(name)
            FROM simple_music_service_artist
                INNER JOIN simple_music_service_database_audit as artist_id
                    ON simple_music_service_artist.id = artist_id.new_value::integer
                INNER JOIN simple_music_service_database_audit as song_artist_id
                    ON artist_id.record_id = song_artist_id.record_id
            WHERE artist_id."table" = 'simple_music_service_song_artist' and artist_id.old_value is NULL
                and artist_id.column_name = 'artist_id' and song_artist_id."table" = 'simple_music_service_song_artist'
                and song_artist_id.old_value is NULL and song_artist_id.column_name = 'song_id'
                and song_artist_id.new_value = song_id.new_value) as song_artist
    FROM simple_music_service_database_audit as audit
        INNER JOIN simple_music_service_database_audit as song_id
            ON audit.record_id = song_id.record_id
        INNER JOIN simple_music_service_database_audit as song_title
            ON song_id.new_value::integer = song_title.record_id
    WHERE audit."table" = 'simple_music_service_comment' and audit.column_name = 'user_id'
        and song_id."table" = 'simple_music_service_comment' and song_id.column_name = 'song_id'
        and song_id.new_value is NOT NULL and song_title."table" = 'simple_music_service_song'
        and song_title.column_name = 'title' and song_title.new_value is NOT NULL and audit.new_value = %(user_id)s
    """
    query_params = {"user_id": user_id}
    get_comments_query, query_params = form_query_and_params_with_date(get_comments_query, query_params,
                                                                       from_date, to_date)
    data = []
    comments = DatabaseAudit.objects.raw(get_comments_query, query_params)
    for comment in comments:
        filter_params = {"table": "simple_music_service_comment", "record_id": comment.id, "column_name": "message"}
        add_date_params_to_filter(filter_params, from_date, to_date)
        messages = DatabaseAudit.objects.filter(**filter_params)
        for message in messages:
            if message.old_value is None:
                description = "Wrote comment for song '{song_title} - {song_artist}' with message '{new_value}'"
            elif message.new_value is not None:
                description = "Changed comment for '{song_title} - {song_artist}' from '{old_value}' to '{new_value}'"
            else:
                description = "Deleted comment for song '{song_title} - {song_artist}' with message '{old_value}'"
            data.append({"event_date_time": message.created_date_time,
                         "description": description.format(song_title=comment.song_title,
                                                           song_artist=", ".join(comment.song_artist),
                                                           new_value=message.new_value, old_value=message.old_value)})
    return data


def form_query_and_params_with_date(query, query_params, from_date, to_date):
    if from_date:
        query += " and audit.created_date_time > %(from_date)s"
        query_params["from_date"] = from_date
    if to_date:
        query += " and audit.created_date_time < %(to_date)s"
        query_params["to_date"] = to_date
    return query, query_params


def add_date_params_to_filter(filter_params, from_date, to_date):
    if from_date:
        filter_params["created_date_time__gte"] = from_date
    if to_date:
        filter_params["created_date_time__lte"] = to_date
