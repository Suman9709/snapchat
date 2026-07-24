
from django.shortcuts import redirect, render
from .form import RegisterForm, LoginForm

from django.views.decorators.http import require_http_methods
from django.contrib.auth import login, logout

from django.contrib.auth.decorators import login_required

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
    return render(request, 'pages/chat.html')
