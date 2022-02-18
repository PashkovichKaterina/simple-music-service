from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken
from django.contrib.auth.models import User
from django.urls import reverse
from .serializers import ArtistSerializer
from .test_factories import ArtistFactory, UserFactory
from .models import Artist


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

    def test_can_read_a_specific_artist(self):
        response = self.client.get(reverse("artist-detail", args=[self.artist.id]))

        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(ArtistSerializer(instance=self.artist).data, response.data)

    def test_can_add_a_new_artist(self):
        self.authorization()

        payload = {"name": "artist test name"}
        response = self.client.post(reverse("artist-list"), payload)
        created_artist = Artist.objects.get(name=payload["name"])

        self.assertEqual(status.HTTP_201_CREATED, response.status_code)
        for key, value in payload.items():
            self.assertEqual(value, response.data[key])
            self.assertEqual(value, getattr(created_artist, key))

    def test_can_delete_an_artist(self):
        self.authorization()

        response = self.client.delete(reverse("artist-detail", args=[self.artist.id]))

        self.assertEqual(status.HTTP_204_NO_CONTENT, response.status_code)
        self.assertFalse(Artist.objects.filter(pk=self.artist.id))

    def authorization(self):
        self.client = APIClient(enforce_csrf_checks=False)
        access = AccessToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")


class SignUpViewSetTest(APITestCase):
    def test_can_sign_up_new_user(self):
        payload = {"username": "testUsername", "password": "test password"}

        response = self.client.post(reverse("signup-list"), payload)
        created_user = User.objects.get(username=payload["username"])

        self.assertEqual(status.HTTP_201_CREATED, response.status_code)
        self.assertEqual(payload["username"], response.data["username"])
        self.assertEqual(payload["username"], getattr(created_user, "username"))


class TokenViewSetTest(APITestCase):
    def test_can_user_sign_in(self):
        self.client.post(reverse("signup-list"), self.payload)

        response = self.client.post(reverse("token"), self.payload)
        signin_user = User.objects.get(username=self.payload["username"])

        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assert_tokens_claims(response, signin_user)

    def test_can_user_refresh_token(self):
        self.client.post(reverse("signup-list"), self.payload)
        response = self.client.post(reverse("token"), self.payload)
        signin_user = User.objects.get(username=self.payload["username"])

        payload = {"refresh": response.data["refresh"]}
        response = self.client.post(reverse("token/refresh"), payload)

        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assert_tokens_claims(response, signin_user)

    @classmethod
    def setUpTestData(cls):
        cls.payload = {"username": "testUsername", "password": "test password"}

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
