from .models import FriendRequest, Conversation
from django.db.models import Q
from django.utils import timezone

def are_friends(user1, user2):
    return FriendRequest.objects.filter(
        Q(from_user=user1, to_user=user2) |
        Q(from_user=user2, to_user=user1),
        status=FriendRequest.StatusChoices.ACCEPTED,
    ).exists()


def update_snap_streak(conversation, sender):
    today = timezone.now().date()
    
    
    # first snap ever
    
    if not conversation.last_snap_date:
        conversation.last_snap_date = today
        conversation.last_snap_send = sender
        conversation.save()
        
        return
    # same person sending again
    
    if conversation.last_snap_send == sender:
        # conversation.last_snap_date = today
        # conversation.save()
        return
    
    # other person send
    
    
    days = (today - conversation.last_snap_date).days
    if days <= 1:
        conversation.streak+=1
    else:
        conversation.streak = 1
    conversation.last_snap_date = today
    conversation.last_snap_send = sender
    
    conversation.save()
        
    
