from django.contrib import admin

from django.contrib.auth.admin import UserAdmin

from snapchat.models import Conversation, FriendRequest, Message, SnapUser

# Register your models here.

# if unable to use the user created by the admin
class MyUserAdmin(UserAdmin):
    model = SnapUser
    fields = UserAdmin.fieldsets+((None, {"fields":("profile_pic","bio")}))
    
    
admin.site.register(FriendRequest)
admin.site.register(Conversation)
admin.site.register(Message)
admin.site.register(SnapUser)

