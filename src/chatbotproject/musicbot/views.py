# from django.shortcuts import render
from django.views import generic
from django.http.response import HttpResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from pprint import pprint
import json
import requests
from .models import Message, Conversation, StateEnum, Track

from django.shortcuts import get_object_or_404


def call_musixmatch_api(service, params):
    base_url = "https://api.musixmatch.com/ws/1.1/"
    api_key = "&apikey=41da9710650383c323dc1f32dabd847d"
    format_url = "?format=json&callback=callback"

    api_call = base_url + service + format_url + params + api_key

    print("API Call: ", api_call)
    return requests.get(api_call)


def search_track(track_query):
    service = "track.search"
    params = "&q_lyrics=" + track_query + "&f_has_lyrics=1" + "&s_track_rating=desc"

    request = call_musixmatch_api(service, params)
    data = request.json()
    data = data['message']['body']

    track_list = [track['track'] for track in data['track_list']]
    # pprint(track_list)
    return track_list


def get_track(track_id):
    service = "track.get"
    params = "&track_id=" + track_id
    request = call_musixmatch_api(service, params)
    
    data = request.json()
    data = data['message']['body']
    return data['track']

def get_lyrics(track_id):
    service = "track.lyrics.get"
    params = "&track_id=" + track_id
    request = call_musixmatch_api(service, params)
    data = request.json()
    data = data['message']['body']
    lyrics = data['lyrics']['lyrics_body']
    print("Lyrics:", lyrics)
    return lyrics

# Menu de inicio
MENU_MSG_1 = "Hola! Soy Musicbot! Un bot para encontrar la letra de tus canciones favoritas!"

MENU_MSG_2 = "Quieres buscar la letra de alguna canción? o prefieres ver algunos reportes de la aplicación?"

MENU_BTN_SEARCH_TITLE = "Buscar letras"
MENU_BTN_SEARCH_PAYLOAD = "MENU_SEARCH"

MENU_BTN_REPORTS_TITLE = "Ver reportes"
MENU_BTN_REPORTS_PAYLOAD = "MENU_REPORTS"


# Menu de busqueda de letra de canciones
MENU_SEARCH_MSG = "Deseas buscar una nueva canción o seleccionar una de tu lista de favoritos?"

MENU_SEARCH_NEW_TITLE = "Nueva canción"
MENU_SEARCH_NEW_PAYLOAD = "NEW_SONG"

MENU_SEARCH_FAV_TITLE = "De favoritos"
MENU_SEARCH_FAV_PAYLOAD = "FAV_SONG_LIST"

# Boton de empezar
GET_STARTED_PAYLOAD = "Empezar"

# Preguntar song query
ASK_SONG_QUERY = "Escribe el nombre de la canción o algunas letras que recuerdes"

NO_TRACKS_FOUND = "No se encontraron canciones :("


class FacebookMessage(object):
    TOKEN = 'EAAcJTOlr3d4BAJtAZBplo14EZBgqzkRZAFLheupz05V8ZAt1EGYNAly0LKZCZBdYr4gBOU3ZCegE6RQ6ixlGhCeKgPbItRnwrLRez8DNrGlZC1mJm9uGDIJXq3nEbY4dZBPxeo1J3GF9CN0She748Pn3yMVFLqICFYEUYQeA6qFsNfoyBwz72dRl5'
    POST_MESSAGE_URL = 'https://graph.facebook.com/v3.1/me/messages?access_token=' + TOKEN

    def __init__(self, sender_id, msg):
        self.sender_id = sender_id
        self.msg = msg

    def get_conversation(self):
        try:
            c = Conversation.objects.get(fb_user_id=self.sender_id)
        except Conversation.DoesNotExist:
            c = None

        return c

    def save_message(self, conversation):
        m = Message.objects.create(conversation=conversation,
                                   text=self.msg)
        m.save()

    def post_message(self, response_msg):
        json_response = json.dumps({
            "recipient": {"id": self.sender_id},
            **response_msg,
        })

        status = requests.post(FacebookMessage.POST_MESSAGE_URL,
                               headers={"Content-Type": "application/json"},
                               data=json_response)
        pprint(status.json())

    def respond_message(self, conversation):
        if conversation.state == str(StateEnum.NEW) or \
           conversation.state == StateEnum.NEW:
            # welcome msg
            response_msg = {
                    "message": {"text": MENU_MSG_1}
                    }

            self.post_message(response_msg)

            # menu options
            response_msg = {
                "message": {
                    "attachment": {
                        "type": "template",
                        "payload": {
                            "template_type": "button",
                            "text": MENU_MSG_2,
                            "buttons": [
                                {
                                    "type": "postback",
                                    "title": MENU_BTN_SEARCH_TITLE,
                                    "payload": StateEnum.SEARCH_LYRICS.value,
                                },
                                {
                                    "type": "postback",
                                    "title": MENU_BTN_REPORTS_TITLE,
                                    "payload": StateEnum.CHECK_REPORTS.value,
                                }
                            ]
                        }
                    }
                }
            }

            self.post_message(response_msg)

            # update state
            conversation.state = StateEnum.GET_STARTED
            conversation.save()

        if conversation.state == str(StateEnum.GET_STARTED):
            if self.msg == StateEnum.SEARCH_LYRICS.value:
                # search options
                response_msg = {
                    "message": {
                        "attachment": {
                            "type": "template",
                            "payload": {
                                "template_type": "button",
                                "text": MENU_SEARCH_MSG,
                                "buttons": [
                                    {
                                        "type": "postback",
                                        "title": MENU_SEARCH_NEW_TITLE,
                                        "payload": StateEnum.SEARCH_NEW_SONG.value,
                                    },
                                    {
                                        "type": "postback",
                                        "title": MENU_SEARCH_FAV_TITLE,
                                        "payload": StateEnum.SEARCH_FROM_FAV.value,
                                    }
                                ]
                            }
                        }
                    }
                }

                self.post_message(response_msg)

                # update state
                conversation.state = StateEnum.SEARCH_LYRICS
                conversation.save()

            if self.msg == StateEnum.CHECK_REPORTS.value:
                # TODO
                # Report menu
                pass

        if conversation.state == str(StateEnum.SEARCH_LYRICS):
            if self.msg == StateEnum.SEARCH_NEW_SONG.value:
                # ask song query
                response_msg = {
                    "message": {
                        "text": ASK_SONG_QUERY,
                    }
                }
                self.post_message(response_msg)

                # update state
                conversation.state = StateEnum.SEARCH_NEW_SONG
                conversation.save()

            if self.msg == StateEnum.SEARCH_FROM_FAV.value:
                track_list = [get_track(track.track_id)
                              for track in Track.objects.filter(
                                conversation=conversation)]

                elements = []
                for track in track_list:
                    elements.append({
                        'title': track['artist_name'],
                        'buttons': [
                            {
                                "type": "postback",
                                "title": track['track_name'],
                                "payload": track['track_id'],
                            }
                        ]
                    })

                if elements:
                    response_msg = {
                        "message": {
                            "attachment": {
                                "type": "template",
                                "payload": {
                                    "template_type": "list",
                                    "top_element_style": "compact",
                                    "elements": elements[:4],
                                }
                            }
                        },
                    }

                    self.post_message(response_msg)
                    conversation.state = StateEnum.SHOW_LYRICS
                    conversation.save()

        if conversation.state == str(StateEnum.SEARCH_NEW_SONG):
            track_list = search_track(self.msg)

            elements = []
            for track in track_list:
                elements.append({
                    'title': track['artist_name'],
                    'buttons': [
                        {
                            "type": "postback",
                            "title": track['track_name'],
                            "payload": track['track_id'],
                        }
                    ]
                })

            if elements:
                response_msg = {
                    "message": {
                        "attachment": {
                            "type": "template",
                            "payload": {
                                "template_type": "list",
                                "top_element_style": "compact",
                                "elements": elements[:4],
                            }
                        }
                    },
                }
                self.post_message(response_msg)
                conversation.state = StateEnum.SHOW_LYRICS
                conversation.save()
            else:
                response_msg = {
                    "message": {"text": NO_TRACKS_FOUND}
                }

                self.post_message(response_msg)
                # update state
                # TODO return to previous

        if conversation.state == str(StateEnum.SHOW_LYRICS):
            lyrics = get_lyrics(self.msg)
            response_msg = {
                    "message": {"text": lyrics}
            }

            self.post_message(response_msg)

            response_msg = {
                "message": {
                    "text": "Desea guardar la canción en la lista de favoritos?",
                    "quick_replies": [
                        {
                            "content_type": "text",
                            "title": "Si",
                            "payload": "Si",
                        },
                        {
                            "content_type": "text",
                            "title": "No",
                            "payload": "No",
                        }
                    ]
                }
            }
            self.post_message(response_msg)

            # update state
            conversation.state = StateEnum.SAVE_TRACK
            conversation.save()

        if conversation.state == str(StateEnum.SAVE_TRACK):
            if self.msg == "Si":

                # Get previous track_id
                # Maybe put a type in message instead of awful "1" index
                track_id = Message.objects.filter(conversation=conversation)[1]

                favorite = Track.objects.create(conversation=conversation,
                                                track_id=track_id.text)
                favorite.save()

                response_msg = {
                        "message": {"text": "Se guardó la canción :)"}
                }
                self.post_message(response_msg)

            # Return to menu options
            response_msg = {
                "message": {
                    "attachment": {
                        "type": "template",
                        "payload": {
                            "template_type": "button",
                            "text": MENU_MSG_2,
                            "buttons": [
                                {
                                    "type": "postback",
                                    "title": MENU_BTN_SEARCH_TITLE,
                                    "payload": StateEnum.SEARCH_LYRICS.value,
                                },
                                {
                                    "type": "postback",
                                    "title": MENU_BTN_REPORTS_TITLE,
                                    "payload": StateEnum.CHECK_REPORTS.value,
                                }
                            ]
                        }
                    }
                }
            }
            self.post_message(response_msg)

            # update state
            conversation.state = StateEnum.GET_STARTED
            conversation.save()

    def handle_message(self):
        print("Message: ", self.msg)
        c = self.get_conversation()

        if not c:
            c = Conversation.objects.create(fb_user_id=self.sender_id,
                                            state=StateEnum.NEW)
            c.save()

        self.save_message(c)
        self.respond_message(c)


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

                if 'message' in message:
                    text = message['message']['text']

                if 'postback' in message:
                    text = message['postback']['payload']

                if text:
                    fbm = FacebookMessage(sender_id, text)
                    fbm.handle_message()

        return HttpResponse()
