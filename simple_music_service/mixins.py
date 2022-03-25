from simple_music_service import serializers
from .models import Rating


class UserMarkMixin:
    def get_user_mark(self, obj):
        if "request" in self.context:
            try:
                user_id = self.context["request"].user.id
                user_mark = Rating.objects.get(song=obj.id, user=user_id)
                return serializers.RatingSerializer().to_representation(user_mark)
            except Rating.DoesNotExist:
                return None
