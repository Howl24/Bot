from django.urls import path
from .views import MusicBotView

urlpatterns = [
    # Secret webhook url
    path('05f129f85fbad4fd4223a922f011f550e3b4c3ab14ddee6588/', MusicBotView.as_view()),
]
