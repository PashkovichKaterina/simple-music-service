from factory.django import DjangoModelFactory, FileField
from factory import Sequence, SubFactory, post_generation
from django.contrib.auth.models import User
from .models import Artist, Song


class ArtistFactory(DjangoModelFactory):
    class Meta:
        model = Artist

    name = Sequence(lambda n: f"artist name {n}")


class UserFactory(DjangoModelFactory):
    class Meta:
        model = User

    username = Sequence(lambda n: f"username{n}")
    password = Sequence(lambda n: f"password{n}")


class SongFactory(DjangoModelFactory):
    class Meta:
        model = Song

    title = Sequence(lambda n: f"song title {n}")
    year = "2020-12-12"
    location = FileField(filename="song.mp3")
    user = SubFactory(UserFactory)

    @post_generation
    def artist(self, create, extracted):
        if not create or not extracted:
            return
        self.artist.add(*extracted)
