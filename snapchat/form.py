from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import SnapUser


class RegisterForm(UserCreationForm):
    class Meta:
        model = SnapUser
        fields = ["username", "password1", "password2"]


class LoginForm(AuthenticationForm):
    pass