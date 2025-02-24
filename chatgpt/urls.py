"""
    This module will hold the url configuration for chatgpt
"""
from django.urls import path
from .views import (
    IncommingMessage, MakeChat, register_view, logout,
    login_request, home,Onboard,chat, chatting,landing_page,
    plan_upgrade, plan_details, checkout,submit_quiz_view,ShowResult,
    terms_and_conditions, privacy_policy, get_started, ImageGenerate, PaymentRedirect,
    QuoteGenerate, HastagsGenerate,ProdiaImageGenerate, Education, profile_page, QuizHome, quiz_start, upload_image
)

urlpatterns = [
    path('upload_image/', upload_image, name='upload_image'),
    path('get_started/', Education.as_view(), name='get_started'),
    path('home/', home, name='home'),
    path('profile/', profile_page, name='profile_page'),
    path('', landing_page, name='landing_page'),
    path('<str:room_name>/<str:username>/<str:chat_with>/', chatting, name='chat_room'),
    path('incomming_message/', IncommingMessage.as_view(), name="incomming_message"),
    path('quiz_home/', QuizHome.as_view(), name="quiz_home"),
    path('quiz/<str:quiz_id>/', quiz_start, name="quiz_start"),
    path('image_generate/', ImageGenerate.as_view(), name="image_generate"),
    path('makechat/',MakeChat.as_view(), name="makechat"),
    path('invite_user/',MakeChat.as_view(), name="invite_user"),
    path('register/',register_view, name="register"),
    path('logout/', logout, name="logout"),
    path('login/', login_request, name="login"),
    path('onboard/', Onboard.as_view(), name="onboard"),
    path("chatting/",chat, name="chatting"),
    path("plan-upgrade/",plan_upgrade, name="plan-upgrade"),
    path("plan-details/",plan_details, name="plan_details"),
    path("checkout/",checkout, name="checkout"),
    path("terms/", terms_and_conditions, name="terms_and_conditions"),
    path("privacy_policy/", privacy_policy, name="privacy_policy"),
    path("payment_redirect/", PaymentRedirect.as_view(), name="payment_redirect"),
    path("quote_generate/",QuoteGenerate.as_view(),name="quote_generate"),
    path("hastag_generate/",HastagsGenerate.as_view(),name="hastag_generate"),
    path("prodia_image_generate/",ProdiaImageGenerate.as_view(),name="prodia_image_generate"),
    path("education/", Education.as_view(), name="education"),
    path('submit_quiz/', submit_quiz_view, name='submit_quiz'),
    path('show_result/', ShowResult.as_view(), name='show_result'),
]
