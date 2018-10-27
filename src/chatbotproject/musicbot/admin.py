from django.contrib import admin

from .models import Conversation, Message, Track

admin.site.register(Conversation)
admin.site.register(Message)
admin.site.register(Track)
#admin.site.register(State)
