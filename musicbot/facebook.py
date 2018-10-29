from . import configuration
from .musixmatch import get_lyrics
from .models import Message, Conversation, StateEnum, Track
import requests
import json
from pprint import pprint
from datetime import timedelta
from django.utils import timezone


class FacebookMessageHandler(object):
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

        status = requests.post(FacebookMessageHandler.POST_MESSAGE_URL,
                               headers={"Content-Type": "application/json"},
                               data=json_response)
        pprint(status.json())

    def get_insights(self):
        # 100 likes to activate this?
        #url = "https://graph.facebook.com/v2.8/me/insights/" + \
        #      "?metric=" + LIST_OF_METRICS + \
        #      "&access_token=" + PAGE_ACCESS_TOKEN
        #data = requests.get(url)
        # data is empty
        # Replacement string generated

        all_users = Conversation.objects.all().count()

        last_week = timezone.now().date() - timedelta(days=7)
        new_users = Conversation.objects.filter(created__gte=last_week).count()

        insights = ["Total de usuarios: "+ str(all_users),
                    "Nuevos usuarios esta semana: " + str(new_users),
                    ]

        return insights


    def get_user_name(self):
        url = "https://graph.facebook.com/" + str(self.sender_id) + \
              "?fields=first_name&access_token=" + \
              configuration.FACEBOOK_MESSENGER_TOKEN

        try:
            data = requests.get(url)
            result = data['first_name']
        except:
            result = ""

        return result

    def respond_message(self, conversation):
        if conversation.state == str(StateEnum.NEW) or \
           conversation.state == StateEnum.NEW:
            # welcome msg
            name = self.get_user_name()

            txt = "Hola, " + name + ". Soy Musicbot! Un bot para encontrar la letra de tus canciones favoritas."

            response_msg = {
                    "message": {"text": txt}
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
                #TODO
                insights = self.get_insights()
                for txt in insights:
                    response_msg = {
                            "message": {
                                "text": txt,
                                }
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
                                            "url": "https://still-ravine-89797.herokuapp.com/musicbot/webview",
                                            "title": "Ver canciones",
                                            "webview_height_ratio": "tall",
                                            "messenger_extensions": "true",
                                            "fallback_url": "https://still-ravine-89797.herokuapp.com/musicbot/webview/",
                                        }
                                        ]
                                    }
                                }
                            }
                }

                self.post_message(response_msg)
                conversation.state = StateEnum.SHOW_LYRICS_FAV
                conversation.save()

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
                                        "url": "https://still-ravine-89797.herokuapp.com/musicbot/webview",
                                        "title": "Ver canciones",
                                        "webview_height_ratio": "tall",
                                        "messenger_extensions": "true",
                                        "fallback_url": "https://still-ravine-89797.herokuapp.com/musicbot/webview/",
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

            # Not empy or None
            if lyrics:
                response_msg = {
                        "message": {"text": lyrics}
                }

                self.post_message(response_msg)
            else:
                response_msg = {
                        "message": {"text": "No pude encontrar letras de esta cancion :("}
                }

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
