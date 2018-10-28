# from django.shortcuts import render
from django.views import generic
from django.http.response import HttpResponse
from django.utils.decorators import method_decorator
from django.views.decorators.clickjacking import xframe_options_exempt
from django.http import JsonResponse

from django.views.decorators.csrf import csrf_exempt
from pprint import pprint
import json
import requests
from .models import Message, Conversation, StateEnum, Track

from django.shortcuts import get_object_or_404
from . import configuration
from .musixmatch import search_track
from .musixmatch import get_track
from .musixmatch import get_lyrics
from .forms import TrackForm


class FacebookMessage(object):
    POST_MESSAGE_URL = configuration.FACEBOOK_POST_MESSAGE_URL

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
                    "message": {"text": configuration.MENU_MSG_1}
                    }

            self.post_message(response_msg)

            # menu options
            response_msg = {
                "message": {
                    "attachment": {
                        "type": "template",
                        "payload": {
                            "template_type": "button",
                            "text": configuration.MENU_MSG_2,
                            "buttons": [
                                {
                                    "type": "postback",
                                    "title": configuration.MENU_BTN_SEARCH_TITLE,
                                    "payload": StateEnum.SEARCH_LYRICS.value,
                                },
                                {
                                    "type": "postback",
                                    "title": configuration.MENU_BTN_REPORTS_TITLE,
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

        elif conversation.state == str(StateEnum.GET_STARTED):
            if self.msg == StateEnum.SEARCH_LYRICS.value:
                # search options
                response_msg = {
                    "message": {
                        "attachment": {
                            "type": "template",
                            "payload": {
                                "template_type": "button",
                                "text": configuration.MENU_SEARCH_MSG,
                                "buttons": [
                                    {
                                        "type": "postback",
                                        "title": configuration.MENU_SEARCH_NEW_TITLE,
                                        "payload": StateEnum.SEARCH_NEW_SONG.value,
                                    },
                                    {
                                        "type": "postback",
                                        "title": configuration.MENU_SEARCH_FAV_TITLE,
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

        elif conversation.state == str(StateEnum.SEARCH_LYRICS):
            if self.msg == StateEnum.SEARCH_NEW_SONG.value:
                # ask song query
                response_msg = {
                    "message": {
                        "text": configuration.ASK_SONG_QUERY,
                    }
                }
                self.post_message(response_msg)

                # update state
                conversation.state = StateEnum.SEARCH_NEW_SONG
                conversation.save()

            if self.msg == StateEnum.SEARCH_FROM_FAV.value:
                response_msg = {
                        "message": {
                            "attachment": {
                                "type": "template",
                                "payload": {
                                    "template_type": "button",
                                    "text": "Selecciona una canción de la lista",
                                    "buttons": [
                                        {
                                            "type": "web_url",
                                            "url": "https://4dbb16ea.ngrok.io/musicbot/webview",
                                            "title": "Ver canciones",
                                            "webview_height_ratio": "tall",
                                            "messenger_extensions": "true",
                                            "fallback_url": "https://4dbb16ea.ngrok.io/musicbot/webview/",
                                        }
                                        ]
                                    }
                                }
                            }
                }

                self.post_message(response_msg)
                conversation.state = StateEnum.SHOW_LYRICS_FAV
                conversation.save()



                #track_list = [get_track(track.track_id)
                #              for track in Track.objects.filter(
                #                conversation=conversation)]

                #elements = []
                #for track in track_list:
                #    elements.append({
                #        'title': track['artist_name'],
                #        'buttons': [
                #            {
                #                "type": "postback",
                #                "title": track['track_name'],
                #                "payload": track['track_id'],
                #            }
                #        ]
                #    })

                #if elements:
                #    response_msg = {
                #        "message": {
                #            "attachment": {
                #                "type": "template",
                #                "payload": {
                #                    "template_type": "list",
                #                    "top_element_style": "full",
                #                    "elements": elements[:4],
                #                }
                #            }
                #        },
                #    }

                #    self.post_message(response_msg)
                #    conversation.state = StateEnum.SHOW_LYRICS
                #    conversation.save()

        elif conversation.state == str(StateEnum.SEARCH_NEW_SONG):
            response_msg = {
                    "message": {
                        "attachment": {
                            "type": "template",
                            "payload": {
                                "template_type": "button",
                                "text": "Selecciona una canción de la lista",
                                "buttons": [
                                    {
                                        "type": "web_url",
                                        "url": "https://4dbb16ea.ngrok.io/musicbot/webview",
                                        "title": "Ver canciones",
                                        "webview_height_ratio": "tall",
                                        "messenger_extensions": "true",
                                        "fallback_url": "https://4dbb16ea.ngrok.io/musicbot/webview/",
                                    }
                                    ]
                                }
                            }
                        }
            }

            self.post_message(response_msg)
            conversation.state = StateEnum.SHOW_LYRICS
            conversation.save()

        elif conversation.state == str(StateEnum.SHOW_LYRICS):
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

        elif conversation.state == str(StateEnum.SHOW_LYRICS_FAV):
            lyrics = get_lyrics(self.msg)
            response_msg = {
                    "message": {"text": lyrics}
            }

            self.post_message(response_msg)

            # menu options
            response_msg = {
                "message": {
                    "attachment": {
                        "type": "template",
                        "payload": {
                            "template_type": "button",
                            "text": configuration.MENU_MSG_2,
                            "buttons": [
                                {
                                    "type": "postback",
                                    "title": configuration.MENU_BTN_SEARCH_TITLE,
                                    "payload": StateEnum.SEARCH_LYRICS.value,
                                },
                                {
                                    "type": "postback",
                                    "title": configuration.MENU_BTN_REPORTS_TITLE,
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

        elif conversation.state == str(StateEnum.SAVE_TRACK):
            if self.msg == "Si":

                # Get previous track_id
                # Maybe put a type in message instead of an awful "1" index
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
                            "text": configuration.MENU_MSG_2,
                            "buttons": [
                                {
                                    "type": "postback",
                                    "title": configuration.MENU_BTN_SEARCH_TITLE,
                                    "payload": StateEnum.SEARCH_LYRICS.value,
                                },
                                {
                                    "type": "postback",
                                    "title": configuration.MENU_BTN_REPORTS_TITLE,
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


class WebView(generic.FormView):
    template_name = "track_list.html"
    form_class = TrackForm
    success_url = "."

    @method_decorator(xframe_options_exempt)
    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def form_valid(self, form):
        # Return response to fb messenger
        sender_id = form.cleaned_data['sender_id']
        track_id = form.cleaned_data['track_id']

        fbm = FacebookMessage(sender_id, track_id)
        fbm.handle_message()

        return super(WebView, self).form_valid(form)

# Ajax track list call
def get_track_list(request):
    sender_id = request.GET.get('sender_id', None)
    conversation = Conversation.objects.get(fb_user_id = sender_id)

    if conversation.state == str(StateEnum.SHOW_LYRICS):
        message = Message.objects.filter(conversation=conversation)[0]
        track_data = search_track(message.text)

        # print(track_list)
        data = {
                'track_list': track_data[:5],
            }
    elif conversation.state == str(StateEnum.SHOW_LYRICS_FAV):
        tracks = Track.objects.filter(conversation=conversation)

        track_data = [get_track(track.track_id)
                      for track in tracks]

        data = {
                'track_list': track_data[:5]
            }

    return JsonResponse(data)
