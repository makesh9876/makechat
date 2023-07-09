"""
    This module will hold the url configuration for chatgpt
"""
from django.urls import path
from .views import (
    IncommingMessage, MakeChat, register_view, logout,
    login_request, home,Onboard,chat, plan_upgrade, plan_details, checkout, payment_success
)

urlpatterns = [
    path('', plan_details, name='plan_details'),
    path('incomming_message/', IncommingMessage.as_view(), name="incomming_message"),
    #path('makechat/',MakeChat.as_view(), name="makechat"),
    #path('invite_user/',MakeChat.as_view(), name="invite_user"),
    #path('register/',register_view, name="register"),
    #path('logout/', logout, name="logout"),
    #path('login/', login_request, name="login"),
    #path('onboard/', Onboard.as_view(), name="onboard"),
    #path("chatting/",chat, name="chatting"),
    path("plan-upgrade/",plan_upgrade, name="plan-upgrade"),
    path("plan-details/",plan_details, name="plan_details"),
    path("checkout/",checkout, name="checkout"),
    path("success/", payment_success, name="payment_success")
]
