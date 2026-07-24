
from django.shortcuts import redirect, render, get_object_or_404
from .form import RegisterForm, LoginForm

from django.views.decorators.http import require_http_methods
from django.contrib.auth import login, logout, get_user_model

from django.contrib.auth.decorators import login_required
from .models import FriendRequest
from django.db.models import Q

# Create your views here.

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
       
@require_http_methods(["GET", "POST"])
def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')
        
    form = LoginForm(request, data=request.POST or None)
    if request.method == 'POST' and form.is_valid():
        login(request, form.get_user())
        return redirect('home')
    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('login')
    
@login_required
def home(request):
    friend_requests = FriendRequest.objects.filter(
        status=FriendRequest.StatusChoices.ACCEPTED
        ).filter(Q(from_user=request.user) | Q(to_user=request.user))
    friends = []
    
    for friend in friend_requests:
        if friend.from_user == request.user:
            friends.append(friend.to_user)
        else:
            friends.append(friend.from_user)
    # all friend
    
    return render(request, 'pages/chat.html', {'friends': friends})

@login_required
def chat(request, id):
    # Implementation for the chat view
    friend = get_object_or_404(get_user_model(), pk=id)
    return render(request, 'pages/chat-details.html', {'friend': friend})

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
    friends = FriendRequest.objects.filter(Q(from_user=request.user, to_user=to_user) | Q(from_user=to_user, to_user=request.user)).exists()
    
    if friends:
        return redirect('search')
    FriendRequest.objects.create(from_user=request.user, to_user=to_user)
    return redirect('search')