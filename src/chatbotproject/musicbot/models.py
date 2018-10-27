from django.db import models
from django_extensions.db.models import TimeStampedModel
from enum import Enum


#class State(models.Model):
#    name = models.CharField(max_length=100)
#    slug = models.SlugField(max_length=50)
#    next_state = models.ForeignKey("self", on_delete=models.CASCADE, null=True, blank=True)
#
#    def __str__(self):
#        return self.name


class StateEnum(Enum):
    NEW = "Nuevo"
    GET_STARTED = "Empezar"
    SEARCH_LYRICS = "Buscar letras"
    CHECK_REPORTS = "Ver reportes"
    SEARCH_NEW_SONG = "Nueva canción"
    SEARCH_FROM_FAV = "De favoritos"
    SHOW_LYRICS = "Mostrar letras"
    SAVE_TRACK = "Guardar en favoritos"

class Conversation(TimeStampedModel):

    fb_user_id = models.CharField(max_length=100)
    #state = models.ForeignKey("State", on_delete=models.CASCADE)
    state = models.CharField(max_length=100,
                             choices=[(tag, tag.value) for tag in StateEnum],
                             )

    class Meta:
        ordering = ['-created']


class Message(TimeStampedModel):
    conversation = models.ForeignKey("Conversation", on_delete=models.CASCADE)
    text = models.CharField(max_length=500,
                            blank=True,
                            null=True,
                            )

    class Meta:
        ordering = ['-created']


class Track(models.Model):
    conversation = models.ForeignKey("Conversation", on_delete=models.CASCADE)
    track_id = models.CharField(max_length=100)
