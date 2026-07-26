
from django.shortcuts import redirect, render, get_object_or_404
from .form import RegisterForm, LoginForm

from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import ensure_csrf_cookie
from django.contrib.auth import login, logout, get_user_model

from django.contrib.auth.decorators import login_required
from .models import FriendRequest, Conversation, Message, Snap, SnapReceiver
from django.db.models import Q
from django.http import JsonResponse
import json
from .utils import are_friends
from django.db import models, transaction
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

# Create your views here.

@ensure_csrf_cookie
@require_http_methods(["GET", "POST"])
def register_view(request):
    if request.user.is_authenticated:
        return redirect('home')
    form = RegisterForm(request.POST or None)
    if request.method =='POST' and form.is_valid():
        user = form.save()
        login(request, user)
        return redirect('home')
    return render(request, 'accounts/register.html', {'form': form})
       
@ensure_csrf_cookie
@require_http_methods(["GET", "POST"])
def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')
        
    form = LoginForm(request, data=request.POST or None)
    if request.method == 'POST' and form.is_valid():
        login(request, form.get_user())
        return redirect('home')
    return render(request, 'accounts/login.html', {'form': form})


    
@ensure_csrf_cookie
@login_required
def home(request):
    friend_requests = FriendRequest.objects.filter(
        status=FriendRequest.StatusChoices.ACCEPTED
        ).filter(Q(from_user=request.user) | Q(to_user=request.user))
    chat_list = []
    
    for fr in friend_requests:
        if fr.from_user == request.user:
            friend = fr.to_user
        else:
            friend = fr.from_user
    # all friend
    
        conversation = (
            Conversation.objects.filter(participants = request.user).filter(participants = friend).first()
        
        )
        last_message = None
        if conversation:
            last_message = (
                conversation.messages.order_by("-created_at").first()
            )
        chat_list.append({
                "friend": friend,
                "conversation": conversation,
                "last_message": last_message,
            })
    chat_list.sort(
    key=lambda chat: (
        chat["last_message"].created_at
        if chat["last_message"]
        else chat["conversation"].created_at
        if chat["conversation"]
        else request.user.date_joined
    ),
    reverse=True,
)
    return render(request, 'pages/chat.html', {'chat_list': chat_list, 'room_name': "general"})


@login_required
def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
@ensure_csrf_cookie
def chat(request, id):
    # Implementation for the chat view
    friend = get_object_or_404(get_user_model(), pk=id)

    if friend == request.user or not are_friends(request.user, friend):
        return redirect('home')
    
    conversation = Conversation.objects.filter(participants = request.user).filter(participants = friend).first()

    if not conversation:
        conversation = Conversation.objects.create()
        conversation.participants.add(request.user, friend)

    messages = conversation.messages.select_related('sender').order_by('created_at')

    return render(request, 'pages/chat-details.html', {
        'friend': friend,
        'conversation': conversation,
        'messages': messages,
    })
    
@require_http_methods(["POST"])
@login_required
def upload_snap(request):
    image = request.FILES.get('image')
    conversation_id = request.POST.get('conversation')
    message_text = request.POST.get('message', '').strip()
    
    if not image:
        return JsonResponse({
            "error":"image not found",
           
        },
            status = 400
            )

    conversation = get_object_or_404(
        Conversation,
        id=conversation_id,
        participants=request.user,
    )
    
    message = Message.objects.create(
        conversation = conversation,
        sender = request.user,
        image = image,
        message = message_text
        
    )
    return JsonResponse({
        'image':message.image.url,
        'message': message.message,
        'id':message.id,
        'created_at':message.created_at.strftime('%H:%M')
    })
    

    
    
# @require_http_methods(["POST"])
# @login_required
# def chat_with_friends(request, friend_id):
    
#     friend = get_user_model().objects.get(pk = friend_id)
    
#     if not friend:
#         return redirect('home')
    
#     messages = Message.objects.filter(
#         Q(sender = request.user, reciever = friend) | Q(sender = friend, reciever = request.user)).order_by('created_at')
        
        
#     messages = list(messages)
#     recieved_messages = Message.objects.filter(sender = friend, reciever = request.user)
#     recieved_messages.delete()
    
#     return render(request, 'pages/chat-details.html', {'friend':friend, 'messages': messages})
    
    
# @login_required
# def send_message(request, friend_id):
#     friend = get_object_or_404(get_user_model(), pk=friend_id)
    
#     if not friend:
#         return redirect('home')
#     message = request.POST.get('message')
#     if message:
#         Message.objects.create(sender=request.user, reciever=friend, message=message)
#     return redirect('chat', friend_id=friend.id)

@ensure_csrf_cookie
@login_required
def search_view(request):
    users = []
    friends = []
    unique_friends = []
    pending = []
    searchusername = request.GET.get('username')
    # find the user with the username that contains the searchusername and exclude the current user
    if searchusername:
        users = (
            get_user_model()
            .objects.filter(username__icontains=searchusername)
            .exclude(id=request.user.id)
            )
    # if the user is friends with the current user, then add them to the friends list no need the to user to send friend request
    queryset = FriendRequest.objects.filter(
        Q(from_user=request.user)| Q(to_user=request.user))
    
    friends = queryset.filter(status=FriendRequest.StatusChoices.ACCEPTED)
    pending_requests = queryset.filter(status=FriendRequest.StatusChoices.PENDING)
    
    # get the users that are friends with the current user
    for friend in friends:
        if request.user == friend.from_user:
            unique_friends.append(friend.to_user.id)
        else:
            unique_friends.append(friend.from_user.id)
    
    for req in pending_requests:
        if request.user == req.from_user:
            pending.append(req.to_user.id)
        else:
            pending.append(req.from_user.id)

    return render(request, 'pages/search.html', {
        'users': users, 
        'friends': unique_friends, 
        'pending': pending,
        'search': searchusername})


@require_http_methods(["POST"])
@login_required
def send_invite(request, id):
    if id == request.user.id:
        return redirect('search')
    to_user = get_object_or_404(get_user_model(), id=id)
    # friends = FriendRequest.objects.filter(Q(from_user=request.user, to_user=to_user) | Q(from_user=to_user, to_user=request.user)).exists()
    
    if are_friends(request.user, to_user):
        return redirect('search')
    FriendRequest.objects.create(from_user=request.user, to_user=to_user)
    return redirect('search')

@require_http_methods(['GET'])
@login_required
def get_all_friend_request(request):
    
    #friendrequest baali table oe chalayenge ek query and cjek karenge ki request.user ka pending friend kon kon h
    friend_requests= FriendRequest.objects.filter(status = FriendRequest.StatusChoices.PENDING, to_user = request.user)
    return render(
        request, 'pages/friend_request.html', {"friend_requests":friend_requests}
    )
    
@require_http_methods(['POST'])
@login_required
def accept_request(request, id):
    req = get_object_or_404(FriendRequest, pk=id)
    if req.to_user == request.user and req.status == FriendRequest.StatusChoices.PENDING:
        req.status = FriendRequest.StatusChoices.ACCEPTED
        req.save()
        return redirect('friend_request')
    return redirect('friend_request')

@require_http_methods(['POST', 'GET'])
@login_required
def user_profile(request):
    # profile = SnapUser.objects.get(id = request.user.id)
    user = request.user
    snap_count = Message.objects.filter(sender = user, image__isnull=False).count()
    
    friend_count = FriendRequest.objects.filter(status=FriendRequest.StatusChoices.ACCEPTED).filter(models.Q(from_user = user) | Q(to_user = user)).count()
    
    return render(request, 'pages/profile.html', {'user':user, 'snap_count':snap_count,'friend_count':friend_count})



@login_required
def edit_user_profile(request):
    return render(request, 'pages/profile-edit.html', {"user":request.user})

@require_http_methods(['POST'])
@login_required
def update_user_profile(request):
    user = request.user
    user.email = request.POST.get("email")
    user.bio = request.POST.get('bio')
    profile_pic = request.FILES.get('profile_pic')

    if(profile_pic):
        user.profile_pic = profile_pic
        
    user.save()
    
    return redirect('profile')


@ensure_csrf_cookie
@login_required
def camera_view(request, id=None):
    friend_requests = FriendRequest.objects.filter(
        status=FriendRequest.StatusChoices.ACCEPTED
    ).filter(
        models.Q(from_user=request.user) | models.Q(to_user=request.user)
    ).select_related('from_user', 'to_user')

    friends = []
    for friend_request in friend_requests:
        if friend_request.from_user == request.user:
            friends.append(friend_request.to_user)
        else:
            friends.append(friend_request.from_user)

    selected_friend = next((friend for friend in friends if friend.id == id), None)

    if id and not selected_friend:
        return redirect('home')

    return render(request, 'pages/camera-v2.html', {
        'friends': friends,
        'selected_friend_id': selected_friend.id if selected_friend else None,
        'direct_friend': selected_friend,
        'is_direct_snap': selected_friend is not None,
    })
    
@require_http_methods(['POST'])
@login_required
def send_snap(request):
    image = request.FILES.get('image')
    receiver_ids = request.POST.getlist('receivers')
    caption = request.POST.get('caption', '').strip()

    if not image:
        return JsonResponse({"error": "image not found"}, status=400)

    if not receiver_ids:
        return JsonResponse({"error": "select at least one friend"}, status=400)

    receivers = get_user_model().objects.filter(id__in=receiver_ids).exclude(id=request.user.id)
    valid_receivers = [
        receiver for receiver in receivers
        if are_friends(request.user, receiver)
    ]

    if not valid_receivers:
        return JsonResponse({"error": "no valid friends selected"}, status=400)

    broadcast_messages = []

    with transaction.atomic():
        snap = Snap.objects.create(
            sender=request.user,
            image=image,
            caption=caption,
        )

        SnapReceiver.objects.bulk_create([
            SnapReceiver(snap=snap, receiver=receiver)
            for receiver in valid_receivers
        ])

        for receiver in valid_receivers:
            conversation = (
                Conversation.objects
                .filter(participants=request.user)
                .filter(participants=receiver)
                .first()
            )

            if not conversation:
                conversation = Conversation.objects.create()
                conversation.participants.add(request.user, receiver)

            message = Message.objects.create(
                conversation=conversation,
                sender=request.user,
                message=caption,
                image=snap.image.name,
            )
            broadcast_messages.append((conversation.id, message))

    channel_layer = get_channel_layer()
    if channel_layer:
        for conversation_id, message in broadcast_messages:
            async_to_sync(channel_layer.group_send)(
                f'chat_{conversation_id}',
                {
                    "type": "chat_message",
                    "message": message.message,
                    "image": message.image.url if message.image else None,
                    "username": request.user.username,
                    "sender_id": request.user.id,
                    "timestamp": message.created_at.strftime("%H:%M"),
                },
            )
    
    return JsonResponse({
        "message": "snap sent",
        "receiver_count": len(valid_receivers),
    })
    
def snap_map(request):
    return render(request, "pages/snapmap.html")


def update_location(request):
    data = json.loads(request.body)
    return JsonResponse({"status": "success"})