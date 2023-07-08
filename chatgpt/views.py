"""
    all the logic is implemented here
"""
#pylint:disable=C0412,E1101,W0127,W0612,W0613,W0621,C0301,W0718
import re
from ramda import path_or
from openai.error import RateLimitError
from rest_framework.views import APIView
from django.views import View
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.core.validators import validate_email
from django.contrib.auth.models import User, auth
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from rest_framework import status
from rest_framework.response import Response
from .models import Customer, UserMessage, InvitedUsers, ChatMessage, ChatThread
from .clients import TwillioClient, OpenApiClient


class DataRetriver:
    """
    handle the user related querues
    """

    def get_user(self, user_name):
        """
        get the user
        """
        try:
            user = User.objects.get(username=user_name)
            return user
        except User.DoesNotExist:
            print("=====user does not exists ", user_name)
            return None

    def get_user_by_user_name(self, user_name: str, create_new_if_not_exists=True):
        """
        get the user onj by user name
        """
        try:
            user = User.objects.get(username=user_name)
            customer = Customer.objects.get(user=user)
            return user, customer
        except User.DoesNotExist:
            print("=====user does not exists ", user_name)
            if create_new_if_not_exists:
                return self.create_new_user(user_name=user_name)
            return None

    def create_new_user(self, user_name: dict):
        """
        This function create new user
        """
        user = User.objects.create_user(username=user_name, password="Speed#123")
        customer = Customer.objects.create(user=user, plan="Free")
        print("=====new user created=>", user)
        return user, customer

    def get_messages_by_user(self, user):
        """
        This function will get the messages of the users
        """
        return UserMessage.objects.filter(user=user).order_by("-created_at")[:10]

    def create_message(self, user, content, role="user"):
        """
        This function create new message
        """
        message = UserMessage.objects.create(user=user, content=content, role=role)
        return message


class ChatGpt:
    """
    handles the chat with chatgpt
    """

    def chat(self, user, messages: list):
        """
        chat with chatgpt
        """
        try:
            open_api_client = OpenApiClient().get_client()
            response = open_api_client.ChatCompletion.create(
                model="gpt-3.5-turbo", messages=messages
            )
            message = path_or("", ["choices", 0, "message", "content"], response)
            DataRetriver().create_message(user=user, content=message, role="system")
            return message
        except RateLimitError as error:
            print("Error", error)
            return "There is a issue at our system, please contact admin to resolve this issue."

    def form_conversations(self, user_messages):
        """
        This function will form the previous messages in conversational format
        """
        messages = []
        for user_msg in user_messages:
            messages.append({"role": user_msg.role, "content": user_msg.content})
        messages.reverse()
        return messages


class OutgoingMessage:
    """
    send message to user
    """

    def send(self, user_number, response_message: str):
        """
        This function will send the message to users
        """
        client = TwillioClient().get_client()
        print("======user number", user_number)
        return client.messages.create(
            from_="whatsapp:+14155238886",
            body="Hey Buddy,\n\nYou have been invited to chat on Makechat! Someone has sent you an anonymous invitation to chat with them. \nHere's the message they sent:\n\n"
            + "============================\n\n"
            + response_message + "\n\n"
             + "============================\n\n"
            + "\n\nJoin the conversation by clicking on the link below:\n"
            + "http://makechattest.com/onboard?phone_number="+user_number
            + "\n\nFeel free to accept the invitation and start chatting. \nRemember, the person who invited you will remain anonymous.\n\nHappy chatting!\nThe Makechat Team",
            to="whatsapp:+91" + user_number,
        )


class IncommingMessage(APIView):
    """
    Handle the incomming message from users
    """

    def post(self, request):
        """
        Handle the post message
        """
        data = request.data.dict()
        print("====message=>", data)
        user_name = path_or("", ["WaId"], data)
        user_name = user_name[2:12] if len(user_name) > 10 else user_name
        content = path_or("", ["Body"], data)
        if not user_name or not content:
            print("==NO MESSAGE FOUND")
            return Response({"status": status.HTTP_200_OK})
        data_retriver = DataRetriver()
        user_obj, customer_obj = data_retriver.get_user_by_user_name(
            user_name=user_name
        )
        data_retriver.create_message(user=user_obj, content=content, role="user")
        old_messages = data_retriver.get_messages_by_user(user=user_obj)
        print("======retrived messages", old_messages)
        response = ChatGpt().chat(
            user=user_obj,
            messages=ChatGpt().form_conversations(user_messages=old_messages),
        )
        send_message = OutgoingMessage().send(
            user_number=str(user_obj.username), response_message=response
        )
        print("message sent->", send_message)

        return Response({"status": status.HTTP_200_OK})

    def get(self, request):
        """
        handles the get request
        """
        return Response({"status": status.HTTP_200_OK})


class MakeChat(View):
    """
    class to handle the make chat function
    """

    def get(self, request):
        """
        return the template for chat invite
        """
        return render(request, "chatgpt/invite_user.html")

    def already_invited(self, invited_users, invite_to_username):
        """
        This function will check if the user is already invited by current user
        """
        for invited_user in invited_users:
            invite_to = invited_user.invite_to
            if invite_to == invite_to_username:
                print("This user already invited================")
                return True
        return False

    def post(self, request):
        """
        post the message to user
        """
        phone_number = request.POST["phoneNumber"]
        message_to_user = request.POST["welcomemessage"]
        current_user_name = request.user.username
        if current_user_name == phone_number:
            return HttpResponse(
                "The invited user " + phone_number + " is your username"
            )
        invites_by_you = InvitedUsers.objects.filter(invite_from=request.user)
        if not self.already_invited(
            invited_users=invites_by_you, invite_to_username=phone_number
        ):
            InvitedUsers.objects.create(
                invite_from=request.user,
                invite_to=str(phone_number),
            )

        OutgoingMessage().send(
            user_number=phone_number,
            response_message=str(message_to_user),
        )

        return redirect("home")


class Onboard(View):
    """
    This class will onboard the new user
    """

    def get(self, request):
        """
        provide template for new user onboard
        """
        user_name = request.GET.get("phone_number")
        existing_user = DataRetriver().get_user(user_name=user_name)
        if existing_user:
            return render(request, "chatgpt/login.html")
        return render(request, "chatgpt/onboard.html", {"user_name": user_name})


def register_view(request):
    """
    Regsiter and login the user
    """
    if request.method == "POST":
        username = request.POST["emailOrPhone"]
        password = request.POST["password"]

        try:
            validate_email(username)
            # If the input is a valid email address, use it as the username
            username = username
        except Exception:
            # If the input is not a valid email address, check if it is a valid phone number
            if re.match(r"^\d{10}$", username):
                # If the input is a valid phone number, use it as the username
                username = username
            else:
                # If the input is not a valid email or phone number,
                # add an error message and return to the registration form
                messages.error(
                    request,
                    "Please enter a valid 10-digit phone number.",
                )
                return redirect("register")

        # Check if the username is already in use
        if User.objects.filter(username=username).exists():
            messages.error(
                request,
                "Uh-oh! It seems like an account with that phone number already exists. Why not try logging in instead? We've got you covered!",
            )
            return redirect("register")

        # Create the user with email or phone as the username and the provided password
        user = User.objects.create_user(username=username, password=password)
        user.set_password(password)
        user.save()
        # Log the user in and redirect them to the home page
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(
                request, "You have been registered and logged in successfully."
            )
            return redirect("home")
    else:
        return render(request, "chatgpt/register.html")

    return render(request, "chatgpt/register.html")


def logout(request):
    """
    logout the user
    """
    auth.logout(request)
    return render(request, "chatgpt/home.html")


def login_request(request):
    """
    Login the users
    """
    if request.method == "POST":
        username = request.POST["emailOrPhone"]
        password = request.POST["password"]

        user = auth.authenticate(username=username, password=password)
        if user is not None:
            auth.login(request, user)
            return redirect("home")
        messages.info(
            request,
            "Oops! It seems like the credentials you provided are invalid. Please double-check and try again. We're here to help you get it right!",
        )
        return render(request, "chatgpt/login.html")

    else:
        return render(request, "chatgpt/login.html")


@login_required
def home(request):
    """
    home page
    """
    user = request.user
    invited_by_you = InvitedUsers.objects.filter(invite_from=user).order_by(
        "-invited_at"
    )
    invited_by_others = InvitedUsers.objects.filter(
        invite_to=str(user.username)
    ).order_by("-invited_at")
    for invite in invited_by_others:
        onboarded = invite.onboarded
        if onboarded:
            continue
        invite_from = DataRetriver().get_user(user_name=invite.invite_from)
        thread_id = str(invite_from.id) + "_" + str(user.id)
        ChatThread.objects.create(
            thread_id=thread_id, first_person=invite_from, second_person=user
        )
        invite.onboarded = True
        invite.save()
    return render(
        request,
        "chatgpt/home.html",
        {"invited_by_you": invited_by_you, "invited_by_others": invited_by_others},
    )


def chat(request):
    """
    start the chat
    """
    invite_id = request.GET.get("invite_id")
    second_person = request.GET.get("second_person")
    if not invite_id and not second_person:
        return redirect("home")
    if second_person:
        person_obj = DataRetriver().get_user(user_name=second_person)
        if not person_obj:
            return HttpResponse("User is not onboarded yet")
        chat_with = person_obj.username
        thread_id = str(request.user.id) + "_" + str(person_obj.id)
    if invite_id:
        invite_obj = InvitedUsers.objects.get(id=invite_id)
        person_obj = DataRetriver().get_user(user_name=invite_obj.invite_from.username)
        if not person_obj:
            return HttpResponse(
                "User is not onboarded yet or user may deactivated their account"
            )
        thread_id = str(person_obj.id) + "_" + str(request.user.id)
        chat_with = "unknown"
    try:
        thread_obj = ChatThread.objects.filter(thread_id=thread_id).first()
    except ChatThread.DoesNotExist:
        return HttpResponse("User is not onboarded yet")

    messages_list = (
        ChatMessage.objects.filter(thread=thread_obj).order_by("-created_at").reverse()
    )
    return render(
        request,
        "chatgpt/room.html",
        {
            "room_name": thread_id,
            "older_messages": messages_list,
            "chat_with": chat_with,
            "current_user": request.user.username,
        },
    )
    # return HttpResponse("chat started between, " + request.user.username + " and " + second_person.username)

# http://127.0.0.1:8000/onboard?phone_number=9442890327


#django
#djangorestframework
#ramda
#twilio
#openai
#channels
#daphne
#channels_redis