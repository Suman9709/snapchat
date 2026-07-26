from .models import FriendRequest
from django.db.models import Q

def are_friends(user1, user2):
    return FriendRequest.objects.filter(
        Q(from_user=user1, to_user=user2) |
        Q(from_user=user2, to_user=user1),
        status=FriendRequest.StatusChoices.ACCEPTED,
    ).exists()
