from django.contrib import admin

from snapchat.models import Conversation, FriendRequest, Message, SnapUser

# Register your models here.
admin.site.register(FriendRequest)
admin.site.register(Conversation)
admin.site.register(Message)
admin.site.register(SnapUser)

