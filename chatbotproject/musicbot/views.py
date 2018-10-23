from django.shortcuts import render
from django.views import generic
from django.http.response import HttpResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from pprint import pprint
import json
import requests


def post_facebook_message(fbid, received_message):
    post_message_url = 'https://graph.facebook.com/v3.1/me/messages?access_token=EAAcJTOlr3d4BAJtAZBplo14EZBgqzkRZAFLheupz05V8ZAt1EGYNAly0LKZCZBdYr4gBOU3ZCegE6RQ6ixlGhCeKgPbItRnwrLRez8DNrGlZC1mJm9uGDIJXq3nEbY4dZBPxeo1J3GF9CN0She748Pn3yMVFLqICFYEUYQeA6qFsNfoyBwz72dRl5'
    response_msg = json.dumps({
        "recipient": {"id": fbid},
        "message": {"text": received_message}
        })
    status = requests.post(post_message_url, headers={"Content-Type": "application/json"}, data=response_msg)
    pprint(status.json())

class MusicBotView(generic.View):
    def get(self, request, *args, **kwargs):
        if self.request.GET['hub.verify_token'] == "8246":
            return HttpResponse(self.request.GET['hub.challenge'])
        else:
            return HttpResponse("Error, invalid token")

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return generic.View.dispatch(self, request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        incoming_message = json.loads(self.request.body.decode('utf-8'))

        for entry in incoming_message['entry']:
            for message in entry['messaging']:
                if 'message' in message:
                    pprint(message)
                    post_facebook_message(message['sender']['id'], message['message']['text'])

        return HttpResponse()
