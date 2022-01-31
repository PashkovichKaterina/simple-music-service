from django.urls import path
from rest_framework.urlpatterns import format_suffix_patterns
from .views import SongListView, SongDetailView

urlpatterns = [
    path('songs/', SongListView.as_view()),
    path('songs/<int:pk>', SongDetailView.as_view()),
]

urlpatterns = format_suffix_patterns(urlpatterns)
