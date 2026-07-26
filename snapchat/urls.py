

from django.urls import path

from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register_view, name='register-user'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    path('profile/', views.user_profile, name='profile'),
    path('edit-profile/', views.edit_user_profile, name='edit-profile'),
    path('update-profile/', views.update_user_profile, name='update-profile'),
    
    path('camera/', views.camera_view, name='camera'),
    path('camera/<int:id>/', views.camera_view, name='friend-camera'),
    path('snapmap/', views.snap_map, name = "snapmap"),
    
    path('search/', views.search_view, name='search'),
    
    path('send_invite/<int:id>/', views.send_invite, name='send-invite'),
    path('chat/<int:id>/', views.chat, name='chat'),
    path('friend_request', views.get_all_friend_request, name ='friend_request' ),
  path(
    'accept-request/<int:id>/',
    views.accept_request,
    name='accept-request'
),
    path('upload-snap/', views.upload_snap, name='upload_snap'),
    path('send-snap/', views.send_snap, name='send-snap'),
    # path('send_message/<int:id>/', views, name='send-message'),
]
