from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken
from django.contrib.auth.models import User
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from moto import mock_s3
import boto3
from .serializers import ArtistSerializer, SongSerializer, PlaylistSerializer
from .test_factories import ArtistFactory, UserFactory, SongFactory, PlaylistFactory
from .models import Artist, Playlist


class ArtistViewSetTest(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.artists = ArtistFactory.create_batch(size=3)
        cls.artist = cls.artists[0]
        cls.user = UserFactory.create()

    def test_can_browse_all_artists(self):
        response = self.client.get(reverse("artist-list"))

        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(len(self.artists), len(response.data))
        for artist in self.artists:
            self.assertIn(ArtistSerializer(instance=artist).data, response.data)

    def test_can_read_specific_artist(self):
        response = self.client.get(reverse("artist-detail", args=[self.artist.id]))

        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(ArtistSerializer(instance=self.artist).data, response.data)

    def test_can_add_new_artist(self):
        authorization(self.client, self.user)

        payload = {"name": "artist test name"}
        response = self.client.post(reverse("artist-list"), payload)
        created_artist = Artist.objects.get(name=payload["name"])

        self.assertEqual(status.HTTP_201_CREATED, response.status_code)
        for key, value in payload.items():
            self.assertEqual(value, response.data[key])
            self.assertEqual(value, getattr(created_artist, key))

    def test_can_delete_artist(self):
        authorization(self.client, self.user)

        response = self.client.delete(reverse("artist-detail", args=[self.artist.id]))

        self.assertEqual(status.HTTP_204_NO_CONTENT, response.status_code)
        self.assertFalse(Artist.objects.filter(pk=self.artist.id))


class SignUpViewSetTest(APITestCase):
    def test_can_sign_up_new_user(self):
        payload = {"username": "testUsername", "password": "test password"}

        response = self.client.post(reverse("signup-list"), payload)
        created_user = User.objects.get(username=payload["username"])

        self.assertEqual(status.HTTP_201_CREATED, response.status_code)
        self.assertEqual(payload["username"], response.data["username"])
        self.assertEqual(payload["username"], getattr(created_user, "username"))


class TokenViewSetTest(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory.create()
        cls.payload = {"username": cls.user.username, "password": "test password"}

    def test_can_user_sign_in(self):
        response = self.client.post(reverse("token"), self.payload)
        signin_user = User.objects.get(username=self.payload["username"])

        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assert_tokens_claims(response, signin_user)

    def test_can_user_refresh_token(self):
        response = self.client.post(reverse("token"), self.payload)
        signin_user = User.objects.get(username=self.payload["username"])

        payload = {"refresh": response.data["refresh"]}
        response = self.client.post(reverse("token/refresh"), payload)

        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assert_tokens_claims(response, signin_user)

    def assert_tokens_claims(self, response, signin_user):
        self.assertIn("access", response.data.keys())
        self.assertIn("refresh", response.data.keys())
        self.assertEqual(
            signin_user.id, AccessToken(response.data["access"])["user_id"]
        )
        self.assertEqual(
            signin_user.username, AccessToken(response.data["access"])["username"]
        )
        self.assertEqual(
            signin_user.id, RefreshToken(response.data["refresh"])["user_id"]
        )
        self.assertEqual(
            signin_user.username, RefreshToken(response.data["refresh"])["username"]
        )


class SongViewSetTest(APITestCase):
    @classmethod
    @mock_s3
    def setUpTestData(cls):
        cls.bucket_name = "simple-music-service-storage"
        s3 = boto3.resource("s3", region_name="us-east-1")
        s3.create_bucket(Bucket=cls.bucket_name)

        cls.songs = SongFactory.create_batch(size=3)
        cls.song = cls.songs[0]
        cls.user = UserFactory.create()

    def test_can_browse_all_songs(self):
        response = self.client.get(reverse("song-list"))

        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(len(self.songs), len(response.data))
        for song in self.songs:
            self.assertIn(SongSerializer(instance=song).data, response.data)

    def test_can_read_specific_song(self):
        response = self.client.get(reverse("song-detail", args=[self.song.id]))

        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(SongSerializer(instance=self.song).data, response.data)

    @mock_s3
    def test_can_add_new_song(self):
        authorization(self.client, self.user)

        s3 = boto3.resource("s3", region_name="us-east-1")
        s3.create_bucket(Bucket=self.bucket_name)

        file_name = "test-song.mp3"
        file_body = "test file body"
        payload = {
            "title": "test song title",
            "year": "2020-12-12",
            "artist_list[0]": "test artist name",
            "location": SimpleUploadedFile(file_name, bytes(file_body, "utf-8"))
        }
        response = self.client.post(reverse("nested-song-list", args=[self.user.id]), payload)

        self.assertEqual(status.HTTP_201_CREATED, response.status_code)
        body = s3.Object(self.bucket_name, file_name).get()["Body"].read().decode("utf-8")
        self.assertEqual(body, file_body)

    def test_can_browse_all_user_songs(self):
        user_id = self.song.user_id
        user_songs = list(filter(lambda song: song.user_id == user_id, self.songs))

        response = self.client.get(reverse("nested-song-list", args=[user_id]))

        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(len(user_songs), len(response.data))
        for song in user_songs:
            self.assertIn(SongSerializer(instance=song).data, response.data)


class PlaylistViewSetTest(APITestCase):
    @classmethod
    @mock_s3
    def setUpTestData(cls):
        cls.user = UserFactory.create()
        cls.user_playlists = PlaylistFactory.create_batch(size=3, user=cls.user)
        cls.all_playlists = PlaylistFactory.create_batch(size=3)
        cls.all_playlists.extend(cls.user_playlists)

        cls.bucket_name = "simple-music-service-storage"
        s3 = boto3.resource("s3", region_name="us-east-1")
        s3.create_bucket(Bucket=cls.bucket_name)
        cls.songs = SongFactory.create_batch(size=3)

    def test_can_browse_all_user_playlists(self):
        authorization(self.client, self.user)

        response = self.client.get(reverse("playlist-list", args=[self.user.id]))

        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(len(self.user_playlists), len(response.data))
        for playlist in self.user_playlists:
            self.assertIn(PlaylistSerializer(instance=playlist).data, response.data)

    def test_can_read_specific_user_playlist(self):
        authorization(self.client, self.user)
        user_playlist = self.user_playlists[0]

        response = self.client.get(reverse("playlist-detail", args=[self.user.id, user_playlist.id]))

        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(PlaylistSerializer(instance=user_playlist).data, response.data)

    def test_can_add_new_playlist(self):
        authorization(self.client, self.user)

        payload = {
            "title": "test playlist title",
            "song": [
                {"id": self.songs[0].id},
                {"id": self.songs[1].id}
            ]
        }
        response = self.client.post(reverse("playlist-list", args=[self.user.id]), payload, format="json")
        created_playlist = Playlist.objects.get(title=payload["title"])

        self.assertEqual(status.HTTP_201_CREATED, response.status_code)
        self.assertEqual(payload["title"], response.data["title"])
        self.assertEqual(len(payload["song"]), len(response.data["song"]))
        self.assertEqual(payload["title"], created_playlist.title)
        self.assertEqual(len(payload["song"]), len(created_playlist.song.all()))
        for i, payload_song in enumerate(payload["song"]):
            self.assertEqual(payload["song"][i]["id"], response.data["song"][i]["id"])
            self.assertEqual(payload["song"][i]["id"], created_playlist.song.all()[i].id)

    def test_can_edit_playlist(self):
        authorization(self.client, self.user)

        playlist_data = {
            "title": "test playlist title",
            "song": [
                {"id": self.songs[0].id},
                {"id": self.songs[1].id}
            ]
        }
        self.client.post(reverse("playlist-list", args=[self.user.id]), playlist_data, format="json")
        created_playlist = Playlist.objects.get(title=playlist_data["title"])

        payload = {
            "song": [
                {"id": self.songs[1].id},
                {"id": self.songs[2].id}
            ]
        }
        response = self.client.patch(
            reverse("playlist-detail", args=[self.user.id, created_playlist.id]), payload, format="json"
        )
        created_playlist.refresh_from_db()
        self.assertEqual(status.HTTP_200_OK, response.status_code)

        self.assertEqual(playlist_data["title"], response.data["title"])
        self.assertEqual(len(payload["song"]), len(response.data["song"]))
        self.assertEqual(playlist_data["title"], created_playlist.title)
        self.assertEqual(len(payload["song"]), len(created_playlist.song.all()))
        for i in range(0, len(payload["song"])):
            self.assertEqual(payload["song"][i]["id"], response.data["song"][i]["id"])
            self.assertEqual(payload["song"][i]["id"], created_playlist.song.all()[i].id)

    def test_can_delete_playlist(self):
        authorization(self.client, self.user)
        user_playlist = self.user_playlists[0]

        response = self.client.delete(reverse("playlist-detail", args=[self.user.id, user_playlist.id]))

        self.assertEqual(status.HTTP_204_NO_CONTENT, response.status_code)
        self.assertFalse(Playlist.objects.filter(pk=user_playlist.id))


def authorization(client, user):
    access = AccessToken.for_user(user)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
