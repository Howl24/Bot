from django.urls import path
from .views import MusicBotView, WebView, get_track_list

urlpatterns = [
    # Secret webhook url
    path('05f129f85fbad4fd4223a922f011f550e3b4c3ab14ddee6588/', MusicBotView.as_view()),
    path('webview/', WebView.as_view()),
    path('ajax/get_track_list/', get_track_list),
]
