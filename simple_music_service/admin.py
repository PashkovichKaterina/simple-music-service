from django.contrib import admin
from .models import Song, Artist, Playlist, Rating, Comment

admin.site.register(Song)
admin.site.register(Artist)
admin.site.register(Playlist)
admin.site.register(Rating)
admin.site.register(Comment)
