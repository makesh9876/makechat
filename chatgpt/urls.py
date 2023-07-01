"""
    This module will hold the url configuration for chatgpt
"""
from django.urls import path
from .views import (
    IncommingMessage, MakeChat, register_view, logout,
    login_request, home,Onboard, lobby,chat
)

urlpatterns = [
    path('', home, name='home'),
    path('incomming_message/', IncommingMessage.as_view(), name="login"),
    path('makechat/',MakeChat.as_view(), name="makechat"),
    path('invite_user/',MakeChat.as_view(), name="invite_user"),
    path('register/',register_view, name="register"),
    path('logout/', logout, name="logout"),
    path('login/', login_request, name="login"),
    path('onboard/', Onboard.as_view(), name="onboard"),
    path('lobby/',lobby, name='lobby'),
    path("chatting/",chat, name="chatting")
]
