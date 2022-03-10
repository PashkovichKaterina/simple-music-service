from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth.models import User
from .models import Song, Artist, Playlist


class ArtistSerializer(serializers.ModelSerializer):
    class Meta:
        model = Artist
        fields = ["id", "name"]


class SongSerializer(serializers.ModelSerializer):
    artist = ArtistSerializer(many=True, read_only=True)
    artist_list = serializers.ListSerializer(
        child=serializers.CharField(max_length=50), write_only=True
    )

    class Meta:
        model = Song
        fields = ["id", "title", "year", "artist", "artist_list", "location"]

    def create(self, validated_data):
        user_id = self.context["request"].user.id
        validated_data["user_id"] = user_id
        artist_list = validated_data.pop("artist_list")
        song = Song.objects.create(**validated_data)
        for artist_name in artist_list:
            try:
                artist = Artist.objects.get(name=artist_name)
            except Artist.DoesNotExist:
                artist = Artist.objects.create(name=artist_name)
            song.artist.add(artist)
        song.save()
        return song


class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        token["username"] = user.username
        token["email"] = user.email

        return token


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "username", "password", "email", "first_name", "last_name")
        extra_kwargs = {
            "password": {"write_only": True},
            "first_name": {"required": False},
            "last_name": {"required": False},
        }

    def create(self, *args, **kwargs):
        return self.__save_user(super().create, *args, **kwargs)

    def update(self, *args, **kwargs):
        return self.__save_user(super().update, *args, **kwargs)

    @staticmethod
    def __save_user(method, *args, **kwargs):
        user = method(*args, **kwargs)
        password = user.password
        user.set_password(password)
        user.save()
        return user


class PlaylistSongSerializer(serializers.ModelSerializer):
    artist = ArtistSerializer(many=True, read_only=True)
    id = serializers.IntegerField()

    class Meta:
        model = Song
        fields = ["id", "title", "year", "artist", "location"]
        extra_kwargs = {
            "title": {"read_only": True},
            "year": {"read_only": True},
            "location": {"read_only": True},
        }


class PlaylistSerializer(serializers.ModelSerializer):
    song = PlaylistSongSerializer(many=True)

    class Meta:
        model = Playlist
        fields = ["id", "title", "song"]

    def create(self, validated_data):
        user_id = self.context["request"].user.id
        validated_data["user_id"] = user_id
        song_data = validated_data.pop("song")
        playlist = Playlist.objects.create(**validated_data)
        self.__save_song(playlist, song_data)
        return playlist

    def update(self, instance, validated_data):
        song_data = validated_data.pop("song")
        instance = super().update(instance, validated_data)
        instance.song.clear()
        self.__save_song(instance, song_data)
        return instance

    @staticmethod
    def __save_song(instance, song_data):
        for song in song_data:
            song = Song.objects.get(**song)
            instance.song.add(song)
        instance.save()
