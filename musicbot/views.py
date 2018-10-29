from django.views import generic
from django.http.response import HttpResponse
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views.decorators.clickjacking import xframe_options_exempt
from django.views.decorators.csrf import csrf_exempt
from .models import Message, Conversation, StateEnum, Track
from .forms import TrackForm
from .musixmatch import search_track
from .musixmatch import get_track
from .facebook import FacebookMessageHandler
import json


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
                    fbm = FacebookMessageHandler(sender_id, text)
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

        fbm = FacebookMessageHandler(sender_id, track_id)
        fbm.handle_message()

        return super(WebView, self).form_valid(form)


# Ajax track list call
def get_track_list(request):
    sender_id = request.GET.get('sender_id', None)
    conversation = Conversation.objects.get(fb_user_id=sender_id)

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
