from django.db import models
from django_extensions.db.models import TimeStampedModel
from enum import Enum

class PayloadEnum(Enum):
    WELCOME = 0
    SEARCH_LYRICS = 1
    SHOW_REPORTS = 2
    
    FAV_LIST = 3
    NO_FAV_LIST = 4
    EMPTY = 5

    SONG_SELECTED = 6
    FAV_SONG_SELECTED = 7
    
    SAVE_FAV = 8
    NO_SAVE_FAV = 9


class StateEnum(Enum):
    WELCOME = 0
    MENU_OPTIONS = 1
    MENU_FAV_LIST = 2
    MENU_LYRICS = 3
    FAV_SONGS = 4
    ASK_SONG_QUERY = 5

    SONG_SELECTED = 6

    MENU_SAVE_FAV = 7




class Conversation(TimeStampedModel):
    fb_user_id = models.CharField(max_length=100)
    state = models.CharField(max_length=1,
                             choices=[(tag.name, tag.value)
                                       for tag in StateEnum],
                             )

    class Meta:
        ordering = ['-created']


class Message(TimeStampedModel):
    conversation = models.ForeignKey("Conversation", on_delete=models.CASCADE)

    text = models.CharField(max_length=500,
                            blank=True,
                            null=True,
                            )

    payload = models.CharField(max_length=100,
                               blank=True,
                               null=True,
                               )
                                
    class Meta:
        ordering = ['-created']


class Track(models.Model):
    conversation = models.ForeignKey("Conversation", on_delete=models.CASCADE)
    track_id = models.CharField(max_length=100)
