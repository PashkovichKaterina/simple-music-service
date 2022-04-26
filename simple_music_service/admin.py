from django.contrib import admin
from .models import Song, Artist, Playlist, Rating, Comment, ApplicationUser
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin

admin.site.register(Song)
admin.site.register(Artist)
admin.site.register(Playlist)
admin.site.register(Rating)
admin.site.register(Comment)
admin.site.unregister(User)


@admin.register(ApplicationUser)
class ApplicationUserAdmin(UserAdmin):
    pass
