from backend import settings
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth.models import User
from .models import Song, Artist, Playlist, Rating, Comment
from .exceptions import AlreadyExistingObjectException
from .mixins import UserMarkMixin


class ArtistSerializer(serializers.ModelSerializer):
    class Meta:
        model = Artist
        fields = ["id", "name"]


class RatingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rating
        fields = ["id", "mark"]

    def create(self, validated_data):
        set_song_and_user_data(self, validated_data)
        if Rating.objects.filter(song=validated_data["song_id"], user=validated_data["user_id"]).exists():
            raise AlreadyExistingObjectException()
        else:
            return super().create(validated_data)

    def update(self, instance, validated_data):
        set_song_and_user_data(self, validated_data)
        instance = Rating.objects.get(song=validated_data["song_id"], user=validated_data["user_id"])
        return super().update(instance, validated_data)


class SongSerializer(serializers.ModelSerializer, UserMarkMixin):
    artist = ArtistSerializer(many=True, read_only=True)
    artist_list = serializers.ListSerializer(
        child=serializers.CharField(max_length=50), write_only=True
    )
    average_rating = serializers.DecimalField(max_digits=2, decimal_places=1, read_only=True)
    user_mark = serializers.SerializerMethodField()
    comments_count = serializers.SerializerMethodField()

    class Meta:
        model = Song
        fields = ["id", "title", "year", "artist", "artist_list", "location", "average_rating", "reviews_count",
                  "user_mark", "comments_count"]

    @staticmethod
    def get_comments_count(obj):
        return Song.objects.get(id=obj.id).comment_set.count()

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


class PlaylistSongSerializer(serializers.ModelSerializer, UserMarkMixin):
    artist = ArtistSerializer(many=True, read_only=True)
    id = serializers.IntegerField()
    average_rating = serializers.DecimalField(max_digits=2, decimal_places=1, read_only=True)
    user_mark = serializers.SerializerMethodField()

    class Meta:
        model = Song
        fields = ["id", "title", "year", "artist", "location", "average_rating", "reviews_count", "user_mark"]
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


class CommentForSongSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    created_date_time = serializers.DateTimeField(format=settings.DATETIME_FORMAT, read_only=True)

    class Meta:
        model = Comment
        fields = ["id", "user", "message", "created_date_time"]

    def create(self, validated_data):
        set_song_and_user_data(self, validated_data)
        return super().create(validated_data)


class CommentForUserSerializer(serializers.ModelSerializer):
    song = SongSerializer(read_only=True)
    created_date_time = serializers.DateTimeField(format=settings.DATETIME_FORMAT, read_only=True)

    class Meta:
        model = Comment
        fields = ["id", "song", "message", "created_date_time"]


def set_song_and_user_data(instance, validated_data):
    user_id = instance.context["request"].user.id
    validated_data["user_id"] = user_id
    song_id = instance.context["request"].parser_context["kwargs"]["songs_pk"]
    validated_data["song_id"] = song_id
