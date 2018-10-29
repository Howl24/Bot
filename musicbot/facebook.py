from . import configuration
from .musixmatch import get_lyrics
from .models import Message, Conversation, StateEnum, Track
import requests
import json
from pprint import pprint


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

                cnt_users = Conversation.objects.all().count()
                report_text = "Número de usuarios: " + str(cnt_users)

                response_msg = {
                        "message": {
                            "text": report_text,
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