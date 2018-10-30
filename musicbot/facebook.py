from . import configuration
from .musixmatch import get_lyrics
from .models import Message, Conversation, StateEnum, Track
import requests
import json
from pprint import pprint
from datetime import timedelta
from django.utils import timezone
from . import configuration
from . import musixmatch
from .models import PayloadEnum
from copy import copy


class Response(object):
    def get_context(self, conversation):
        """Allow to update variables using the conversation context"""
        pass

    def build_response_data(self, conversation):
        """Build a response data dictionary"""
        raise NotImplementedError

    def post_message(self, response_data):
        """Post response to Messenger """
        json_response = json.dumps(response_data)

        status = requests.post(configuration.FACEBOOK_POST_MESSAGE_URL,
                               headers={"Content-Type": "application/json"},
                               data=json_response)
        pprint(status.json())

    def send_to(self, conversation):
        """Send response to Messenger using the conversation context"""
        self.get_context(conversation)
        response_data = self.build_response_data(conversation)
        self.post_message(response_data)


class QuickResponse(Response):
    def __init__(self, text, response_list):
        self.text = text
        self.response_list = response_list  # (response, payload) list

    def build_response_data(self, conversation):
        response_data = {
            "recipient": {"id": conversation.fb_user_id},
            "message": {
                "text": self.text,
                "quick_replies": [
                    {
                    "content_type": "text",
                    "title": response,
                    "payload": payload,
                    }
                for response, payload in self.response_list]
            }
        }

        return response_data


class TextResponse(Response):
    def __init__(self, response_text):
        self.response_text = response_text

    def build_response_data(self, conversation):
        response_data = {
            "recipient": {"id": conversation.fb_user_id},
            "message": {"text": self.response_text}
        }
        return response_data


class NamedTextResponse(TextResponse):
    def get_context(self, conversation):
        url = "https://graph.facebook.com/{sender_id}?fields=first_name&access_token={token}"
        url = url.format(sender_id=conversation.fb_user_id,
                         token=configuration.FACEBOOK_MESSENGER_TOKEN)

        data = requests.get(url).json()

        try:
            name = data['first_name']
        except KeyError:
            name = ""

        # check TextResponse for "response_text" attribute
        self.response_text = self.response_text.format(name=name)


class WebviewResponse(Response):
    def __init__(self, text, title, url, webview_height_ratio):
        self.text = text
        self.title = title
        self.url = url
        self.ratio = webview_height_ratio

    def build_response_data(self, conversation):
        response_data = {
            "recipient": {"id": conversation.fb_user_id},
            "message": {
                "attachment": {
                    "type": "template",
                    "payload": {
                        "template_type": "button",
                        "text": self.text,
                        "buttons": [
                            {
                                "type": "web_url",
                                "url": self.url,
                                "title": self.title,
                                "webview_height_ratio": self.ratio,
                                "messenger_extensions": "true",
                                "fallback_url": self.url,  # Is this ok?
                            }
                            ]
                        }
                }
            }
        }
        return response_data

class IdWebviewResponse(WebviewResponse):
    def get_context(self, conversation):
        self.url = self.url.format(sender_id=conversation.fb_user_id)

class ResponseCollection(object):
    """
    Simple Response wrapper with send_to method.
    """

    def __init__(self, responses):
        self.responses = responses

    def send_to(self, conversation):
        for response in self.responses:
            response.send_to(conversation)

class ReportResponseCollection(ResponseCollection):

    def __init__(self, responses_template):
        self.responses_template = responses_template

    def send_to(self, conversation):
        self.responses = []

        cnt_users = Conversation.objects.all().count()

        self.responses = copy(self.responses_template)
        self.responses[0].response_text = self.responses_template[0].response_text.format(
                number = cnt_users)

        last_week = timezone.now().date() - timedelta(days=7)
        new_users = Conversation.objects.filter(created__gte=last_week).count()

        self.responses[1].response_text = self.responses_template[1].response_text.format(
                number = new_users)


        searchs = Message.objects.filter(payload=PayloadEnum.SEARCH_LYRICS.name).count()
        self.responses[2].response_text = self.responses_template[2].response_text.format(
                number= searchs)

        super().send_to(conversation)


class MessageHandler(object):
    def __init__(self):
        self.responses = {}

    def set_response(self, text, response, next_state):
        self.responses[text] = (response, next_state)

    def handle_message(self, text, payload, conversation):
        Message.objects.create(conversation=conversation,
                               text=text,
                               payload=payload)

        # payload priority over text
        if payload in self.responses:
            response, new_state = self.responses[payload]
        elif text in self.responses:
            response, new_state = self.responses[text]
        else:
            response = TextResponse("Vuelve a intentar")
            new_state = conversation.state

        response.send_to(conversation)
        conversation.state = new_state
        conversation.save()


class SaveSongMessageHandler(MessageHandler):

    def handle_message(self, text, payload, conversation):
        if payload == PayloadEnum.SAVE_FAV.name:
            track_msg = Message.objects.filter(conversation=conversation)[:1].get()

            Track.objects.create(conversation=conversation,
                                 track_id = track_msg.text)

        super().handle_message(text, payload, conversation)
