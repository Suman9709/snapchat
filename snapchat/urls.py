

from django.urls import path

from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register_view, name='register-user'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('search/', views.search_view, name='search'),
    path('send_invite/<int:id>/', views.send_invite, name='send-invite'),
    path('chat/<int:id>/', views.chat, name='chat'),
]
