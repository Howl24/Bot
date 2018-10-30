from django.views import generic
from django.views.generic.edit import FormMixin
from django.http.response import HttpResponse
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views.decorators.clickjacking import xframe_options_exempt
from django.views.decorators.csrf import csrf_exempt
from .models import Message, Conversation, StateEnum, Track, PayloadEnum
from .forms import TrackForm
from .musixmatch import search_track
from .musixmatch import get_track
from . import musixmatch
import json
from .facebook import (MessageHandler,
                       TextResponse,
                       NamedTextResponse,
                       QuickResponse,
                       ResponseCollection,
                       ReportResponseCollection,
                       WebviewResponse,
                       IdWebviewResponse,
                       SaveSongMessageHandler,
                       )

# StateEnum.WELCOME
welcomeMH = MessageHandler()
welcomeMH.set_response(
        PayloadEnum.WELCOME.name,
        ResponseCollection([
            NamedTextResponse("Hola {name} :) Bienvenido a Musixbot!"),
            QuickResponse("Que deseas hacer?", [
                ("Buscar canciones", PayloadEnum.SEARCH_LYRICS.name),
                ("Ver reportes", PayloadEnum.SHOW_REPORTS.name)
            ]),
        ]),
        StateEnum.MENU_OPTIONS.name)

# StateEnum.MENU_OPTIONS
menuOptionsMH = MessageHandler()
menuOptionsMH.set_response(
        PayloadEnum.SEARCH_LYRICS.name,
        QuickResponse("Ver lista de favoritos?",[
            ("Si", PayloadEnum.FAV_LIST.name),
            ("No", PayloadEnum.NO_FAV_LIST.name)
        ]),
        StateEnum.MENU_FAV_LIST.name)

menuOptionsMH.set_response(
        PayloadEnum.SHOW_REPORTS.name,
        ReportResponseCollection([
            TextResponse("Total de usuarios: {number}"),
            TextResponse("Nuevos usuarios esta semana: {number}"),
            TextResponse("Búsquedas en la semana: {number}"),
            QuickResponse("Que deseas hacer?", [
                ("Buscar canciones", PayloadEnum.SEARCH_LYRICS.name),
                ("Ver reportes", PayloadEnum.SHOW_REPORTS.name)
            ]),
        ]),
        StateEnum.MENU_OPTIONS.name)

# StateEnum.MENU_FAV_LIST
menuFavListMH = MessageHandler()
menuFavListMH.set_response(
        PayloadEnum.FAV_LIST.name,
        IdWebviewResponse(
            "Seleccione una canción.",
            "Ver canciones",
            "https://still-ravine-89797.herokuapp.com/musicbot/songlistview/fav/{sender_id}/",
            "tall"),
        StateEnum.SONG_SELECTED.name)

menuFavListMH.set_response(
        PayloadEnum.NO_FAV_LIST.name,
        ResponseCollection([
            TextResponse("Hora de buscar una canción!"),
            TextResponse("Dime el nombre de la canción o del artista"),
            TextResponse("Si recuerdas algunas palabras de la canción también puedes indicarla"),
        ]),
        StateEnum.ASK_SONG_QUERY.name)


# StateEnum.ASK_SONG_QUERY
askSongQueryMH = MessageHandler()
askSongQueryMH.set_response(
        PayloadEnum.EMPTY.name,
        IdWebviewResponse(
            "Seleccione una canción.",
            "Ver canciones",
            "https://still-ravine-89797.herokuapp.com/musicbot/songlistview/nofav/{sender_id}",
            "tall"),
        StateEnum.SONG_SELECTED.name)

# StateEnum.SONG_SELECTED
selectedSongMH = MessageHandler()
selectedSongMH.set_response(
        PayloadEnum.SONG_SELECTED.name,
        ResponseCollection([
            TextResponse("lyrics"),
            QuickResponse("Guardar la canción en la lista de favoritos?", [
                ("Si", PayloadEnum.SAVE_FAV.name),
                ("No", PayloadEnum.NO_SAVE_FAV.name),
            ]),
        ]),
        StateEnum.MENU_SAVE_FAV.name)

selectedSongMH.set_response(
        PayloadEnum.FAV_SONG_SELECTED.name,
        ResponseCollection([
            TextResponse("lyrics"),
            QuickResponse("Que deseas hacer?", [
                ("Buscar canciones", PayloadEnum.SEARCH_LYRICS.name),
                ("Ver reportes", PayloadEnum.SHOW_REPORTS.name)
            ]),
        ]),
        StateEnum.MENU_OPTIONS.name)

menuSaveFavMH = SaveSongMessageHandler()
menuSaveFavMH.set_response(
        PayloadEnum.SAVE_FAV.name,
        ResponseCollection([
            TextResponse("Listo!"),
            QuickResponse("Que deseas hacer?", [
                ("Buscar canciones", PayloadEnum.SEARCH_LYRICS.name),
                ("Ver reportes", PayloadEnum.SHOW_REPORTS.name)
            ]),
        ]),
        StateEnum.MENU_OPTIONS.name)

menuSaveFavMH.set_response(
        PayloadEnum.NO_SAVE_FAV.name,
        QuickResponse("Que deseas hacer?", [
            ("Buscar canciones", PayloadEnum.SEARCH_LYRICS.name),
            ("Ver reportes", PayloadEnum.SHOW_REPORTS.name)
        ]),
        StateEnum.MENU_OPTIONS.name)

MH = {}
MH[StateEnum.WELCOME.name] = welcomeMH
MH[StateEnum.MENU_OPTIONS.name] = menuOptionsMH
MH[StateEnum.MENU_FAV_LIST.name] = menuFavListMH
MH[StateEnum.ASK_SONG_QUERY.name] = askSongQueryMH
MH[StateEnum.SONG_SELECTED.name] = selectedSongMH
MH[StateEnum.MENU_SAVE_FAV.name] = menuSaveFavMH



class MusicBotView(generic.View):
    def get(self, request, *args, **kwargs):
        if self.request.GET['hub.verify_token'] == "8246":   # Webhook Token
            return HttpResponse(self.request.GET['hub.challenge'])
        else:
            return HttpResponse("Error, invalid token")

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return generic.View.dispatch(self, request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        incoming_message = json.loads(self.request.body.decode('utf-8'))

        # Facebook recommends going through every entry since they might send
        # multiple messages in a single call during high load
        for entry in incoming_message['entry']:
            for message in entry['messaging']:
                sender_id = message['sender']['id']
                text = ""
                payload = PayloadEnum.EMPTY.name

                if 'postback' in message:
                    payload = message['postback']['payload']
                    text = message['postback']['title']

                elif 'message' in message:
                    text = message['message']['text']

                    if "quick_reply" in message['message']:
                        payload = message['message']['quick_reply']['payload']

                if text:
                    print("Text: ", text)
                    print("Payload: ", payload)
                    try:
                        c = Conversation.objects.get(fb_user_id=sender_id)
                    except Conversation.DoesNotExist:
                        c = Conversation.objects.create(
                                fb_user_id=sender_id,
                                state=StateEnum.WELCOME.name)

                    print("State: ", c.state)
                    print(MH[c.state])
                    MH[c.state].handle_message(text, payload, c)

        return HttpResponse()


class SongListView(generic.ListView,
                   generic.edit.FormMixin,
                   generic.edit.ProcessFormView):

    template_name = "track_list.html"
    form_class = TrackForm
    success_url = "."

    def get_queryset(self):
        sender_id = self.kwargs['sender_id']
        query_type = self.kwargs['fav']

        if query_type == "fav":
            c = Conversation.objects.get(fb_user_id = sender_id)
            tracks = Track.objects.filter(conversation=c)

            track_list = [get_track(track.track_id)
                          for track in tracks]
        else:
            last_msg = Message.objects.all()[:1].get()
            track_list = musixmatch.search_track(last_msg.text)

        return track_list[:5]

    @method_decorator(xframe_options_exempt)
    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def form_valid(self, form):
        sender_id = form.cleaned_data['sender_id']
        track_id = form.cleaned_data['track_id']

        query_type = self.kwargs['fav']
        if query_type == "fav":
            payload = PayloadEnum.FAV_SONG_SELECTED.name
        else:
            payload = PayloadEnum.SONG_SELECTED.name

        lyrics = musixmatch.get_lyrics(track_id)

        c = Conversation.objects.get(fb_user_id=sender_id)

        # Check vs LyricsTextResponse with conversation query
        #  and lyrics by last message
        MH[c.state].responses[payload][0].responses[0].response_text = lyrics

        # Simulate a Messenger message
        MH[c.state].handle_message(track_id, payload, c)

        return super(SongListView, self).form_valid(form)
