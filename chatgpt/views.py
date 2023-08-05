"""
    all the logic is implemented here
"""
# pylint:disable=C0412,E1101,W0127,W0612,W0613,W0621,C0301,W0718
import re
import json
import urllib
from functools import lru_cache
from datetime import timedelta
from django.http import JsonResponse
from django.urls import reverse
from django.utils import timezone
from ramda import path_or
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
from .lib.chatgpt import ChatGpt
from .lib.payments import PaymentLinks
from .lib.twillio import OutgoingMessage

TEXT_CHAT_LIMIT_FOR_FREE = 20
IMAGE_CHAT_LIMIT_FOR_FREE = 2

PLAN_DETAILS = {
    "24": {
        "plan_name": "Speedy Delight",
        "amount": 5,
        "plan_id": 24,
        "duration": 24,
        "image_quota": 3,
    },
    "168": {
        "plan_name": "Week-long Wackiness",
        "amount": 25,
        "plan_id": 168,
        "duration": 168,
        "image_quota": 13,
    },
    "672": {
        "plan_name": "Monthly plan",
        "amount": 75,
        "plan_id": 672,
        "duration": 672,
        "image_quota": 40,
    },
}


def terms_and_conditions(request):
    """
    render the terms and conditions
    """
    return render(request, "chatgpt/terms.html")


def privacy_policy(request):
    """
    render the privacy policy
    """
    return render(request, "chatgpt/privacy.html")


def get_started(request):
    """
    render the privacy policy
    """
    return render(request, "chatgpt/get_started.html")


def checkout(request):
    """
    This function handle the checkout
    """
    plan_id = request.GET.get("plan_id")
    if not plan_id:
        return HttpResponse("Plan not selected")
    context = PLAN_DETAILS[plan_id]
    return render(request, "chatgpt/checkout.html", context)


def plan_details(request):
    """
    show the plan details
    """
    return render(request, "chatgpt/plans.html")


def plan_upgrade(request):
    """
    This function will upgrade the plan
    """
    phone_number = request.POST["phoneNumber"]
    user_obj = DataRetriver().get_user(user_name=phone_number)
    plan_id = request.GET.get("plan_id")
    if not phone_number or not phone_number or not user_obj:
        return HttpResponse("Phone number or plan id to activate is not identified")
    plan_data = PLAN_DETAILS[plan_id]
    data = {
        "amount": path_or(0, ["amount"], plan_data) * 100,
        "phone_number": phone_number,
        "plan_id": plan_id,
    }
    generate_link_data = PaymentLinks().generate_link(data=data)
    context = {
        "show_amount": (path_or(500, ["amount"], generate_link_data) / 100),
        "user_number": phone_number,
        "plan_id": plan_id,
        "plan_name": path_or("", ["plan_name"], plan_data),
        "link": path_or("", ["short_url"], generate_link_data),
    }
    return render(request, "chatgpt/payment.html", context)


class PaymentRedirect(View):
    """
    This class complete the payments
    """

    def get(self, request):
        """
        complete the payments
        """
        phone_number = request.GET.get("phone_number")
        plan_id = request.GET.get("plan_id")
        razorpay_payment_link_status = request.GET.get("razorpay_payment_link_status")
        if razorpay_payment_link_status != "paid":
            return HttpResponse("Unexpected Error happened, please contact admin")
        DataRetriver().change_plan(username=phone_number, plan_id=plan_id)
        return redirect("get_started")


class ShowResult(View):
    """
    show the result
    """

    def get_formatted_json(self, data: dict):
        """
        this function return the result json in format
        """
        answers = path_or({}, ["response", "answers"], data)
        questions = path_or({}, ["response", "questions"], data)
        my_answer = []
        total_question = len(questions)
        score = 0
        for each_question in questions:
            quest = path_or("", ["text"], each_question)
            correct_answer = next(
                filter(
                    lambda answer: answer.get("is_correct") == "true",
                    each_question["options"],
                ),
                None,
            )
            user_answer = path_or("", [quest], answers)
            is_pass = user_answer == correct_answer["text"]
            if is_pass:
                score += 1
            my_answer.append(
                {
                    "quest": quest,
                    "correct_answer": correct_answer["text"],
                    "user_answer": user_answer,
                    "is_pass": is_pass,
                }
            )
        return {"data": my_answer, "score": str(score) + "/" + str(total_question)}

    def get(self, request):
        """
        get request
        """
        data_param = request.GET.get("data")
        if data_param:
            try:
                data_dict = json.loads(urllib.parse.unquote(data_param))
                res = self.get_formatted_json(data=data_dict)
                return render(request, "chatgpt/show_result.html", {"data_dict": res})
            except json.JSONDecodeError:
                redirect("education")
        return render(request, "chatgpt/show_result.html")


def submit_quiz_view(request):
    """
    submit the quize
    """
    if request.method == "POST":
        data = request.body.decode("utf-8")
        json_data = json.loads(data)
        url = reverse("show_result")
        data = {"success": True, "response": json_data, "redirect_url": url}
        return JsonResponse(data)


@lru_cache
def get_gpt_response(prompt: str):
    """
    return res
    """
    return ChatGpt().completions(promt=prompt)


class Education(View):
    """
    This class handle the education geneate
    """

    def get_prompt(self, category: str):
        """
        this function generate a promt for gpt
        """
        first = "i want you to act as a teacher with skills in all education, and reply with 10 questions with 4 options of each question, your reply should be in json format, do not reply anything other than json.The json format is below,"
        format_res = {
            "prompt": "my_prompt",
            "questions": [
                {
                    "text": "1 st question",
                    "options": [
                        {"text": "option 1", "is_correct": "false"},
                        {"text": "option 2", "is_correct": "false"},
                        {"text": "option 3", "is_correct": "false"},
                        {"text": "option 4", "is_correct": "true"},
                    ],
                }
            ],
        }
        explanation = "reply format should be json parseable by python json loads and use double quotes for string"
        prompt = " your prompt is : " + category
        return first + explanation + str(format_res) + prompt

    def get(self, request):
        """
        render the quote generator
        """
        return render(request, "chatgpt/image_generate.html")

    def post(self, request):
        """
        generate a instagram quote
        """
        try:
            category = request.POST["category"]
            if not category:
                return render(request, "chatgpt/image_generate.html")
            prompt = self.get_prompt(
                category=category,
            )
            chatgpt_response = get_gpt_response(prompt=prompt)
            context = {
                "category": category,
                "response": json.loads(chatgpt_response),
                "result_type": "quote",
                "try_url_name": "quote_generate",
            }
            return render(request, "chatgpt/questions.html", context)
        except Exception as error:
            print("Error -> ", error)
            return HttpResponse("Oops! Something unexpected happened while processing your request. Don't worry, our team has been notified and is working to fix it. Please try again later or contact support(techveins01@gmail.com) if the issue persists. Thank you for your understanding!")


class ProdiaImageGenerate(View):
    """
    This class handle the quote geneate
    """

    def get(self, request):
        """
        render the quote generator
        """
        return render(request, "chatgpt/image_generate.html")

    def post(self, request):
        """
        generate a instagram quote
        """
        image_prompt = request.POST["image_prompt"]
        if not image_prompt:
            return render(request, "chatgpt/image_generate.html")

        image_url = Prodia().image(prompt=image_prompt)
        context = {
            "category": image_prompt,
            "image_url": image_url,
            "result_type": "quote",
            "try_url_name": "quote_generate",
        }
        print(context, "2222222222222")
        return render(request, "chatgpt/generate_results.html", context)


class QuoteGenerate(View):
    """
    This class handle the quote geneate
    """

    def get_prompt(self, category: str, quantity: str):
        """
        this function generate a promt for gpt
        """
        default = "create a quote for instagram post with roughly "
        no_of_words = str(quantity) + "words"
        category = " about this word " + category
        assumption = " only reply the quote in sentence"
        return default + no_of_words + category + assumption

    def get(self, request):
        """
        render the quote generator
        """
        return render(request, "chatgpt/quote_generator.html")

    def post(self, request):
        """
        generate a instagram quote
        """
        category = request.POST["category"]
        quantity = request.POST["quantity"]
        if not category:
            return render(request, "chatgpt/quote_generator.html")
        prompt = self.get_prompt(category=category, quantity=quantity)

        chatgpt_response = ChatGpt().completions(promt=prompt)
        context = {
            "category": category,
            "response": chatgpt_response,
            "result_type": "quote",
            "try_url_name": "quote_generate",
        }
        return render(request, "chatgpt/generate_results.html", context)


class HastagsGenerate(View):
    """
    This class handle the hastags geneate
    """

    def get_prompt(self, category: str, quantity: str):
        """
        this function generate a promt for gpt
        """
        default = "create " + str(quantity) + " hastags for instagram post"
        category = " about this word " + category
        assumption = " only reply the hastags in paragraph format, do not reply any explanation or anything only reply the hastags"
        set_example = " for example , for travle reply should be #WanderlustAdventures #ExploreTheWorld #GlobetrotterLife #TravelGoals #RoamFree"
        return default + category + assumption + set_example

    def get(self, request):
        """
        render the quote generator
        """
        return render(request, "chatgpt/hastag_generate.html")

    def post(self, request):
        """
        generate a instagram quote
        """
        category = request.POST["category"]
        quantity = request.POST["quantity"]
        if not category:
            return render(request, "chatgpt/hastag_generate.html")
        prompt = self.get_prompt(category=category, quantity=quantity)

        chatgpt_response = ChatGpt().completions(promt=prompt)
        context = {
            "category": category,
            "response": chatgpt_response,
            "result_type": "hastag",
            "try_url_name": "hastag_generate",
        }
        return render(request, "chatgpt/generate_results.html", context)


class DataRetriver:
    """
    handle the user related querues
    """

    def change_plan(self, username, plan_id):
        """
        This function will change the plan to active
        """
        user_obj, customer_obj = DataRetriver().get_user_by_user_name(
            user_name=username
        )
        plan_data = path_or({}, [plan_id], PLAN_DETAILS)
        customer_obj.plan = "Standard"
        current_image_quota = customer_obj.image_quota
        new_image_quota = current_image_quota + path_or(0, ["image_quota"], plan_data)
        customer_obj.image_quota = new_image_quota
        expires_at = customer_obj.plan_expires_at
        now = timezone.now()
        print("Time now -->", now)
        print("PLan expires time-->", expires_at)
        if expires_at < now:
            calculate_time_from = now
        else:
            calculate_time_from = expires_at
        plan_duration = path_or(24, ["duration"], plan_data)
        new_expires_at = calculate_time_from + timedelta(hours=plan_duration)
        print("The new expires at -->", plan_data, new_expires_at)
        customer_obj.plan_expires_at = new_expires_at
        customer_obj.save()
        return new_expires_at

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
        except (User.DoesNotExist, Customer.DoesNotExist):
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
        return UserMessage.objects.filter(user=user).order_by("-created_at")

    def create_message(self, user, content, role="user", message_type="text"):
        """
        This function create new message
        """
        message = UserMessage.objects.create(
            user=user, content=content, role=role, message_type=message_type
        )
        return message


def makechat_body(response_message: str, user_number: str):
    """
    This function will return the makechat app body
    """
    return (
        "Hey Buddy,\n\nYou have been invited to chat on Makechat! Someone has sent you an anonymous invitation to chat with them. \nHere's the message they sent:\n\n"
        + "============================\n\n"
        + response_message
        + "\n\n"
        + "============================\n\n"
        + "\n\nJoin the conversation by clicking on the link below:\n"
        + "http://makechattest.com/onboard?phone_number="
        + user_number
        + "\n\nFeel free to accept the invitation and start chatting. \nRemember, the person who invited you will remain anonymous.\n\nHappy chatting!\nThe Makechat Team"
    )


class ImageGenerate(View):
    """
    generate image
    """

    def post(self, request):
        """
        handle the post request
        """
        data = request.data.dict()
        image_prompt = path_or("", ["Body"], data)
        # image_url = ChatGpt().generate_image(image_prompt=image_prompt)
        image_url = Prodia().image(prompt=image_prompt)
        print("33333333333333", image_url)
        return Response({"status": status.HTTP_200_OK})


class IncommingMessage(APIView):
    """
    Handle the incomming message from users
    """

    def send_limit_exceeded_on_free_plan(self, user_obj):
        """
        send limit exceeded msg on free plan
        """
        OutgoingMessage().send(
            user_number=str(user_obj.username),
            response_message="Oops! It seems that you have reached the limit of our free plan for the past 24 hours, with a total of "
            + str(TEXT_CHAT_LIMIT_FOR_FREE)
            + " text message or "
            + str(IMAGE_CHAT_LIMIT_FOR_FREE)
            + " image request"
            + " messages used during this period.\n"
            + "However, you can still continue using our free plan and enjoy limited chatting. Please note that the limit is based on a 24-hour timeframe, and after this period, your message count will reset.\n",
        )

        return True

    #             + "If you wish to have unlimited chatting without interruptions, you can consider upgrading to our affordable plan for just 5 Rs.\n"
    # + "Upgrading is entirely optional, and you can choose to do so at any time. Stay connected and keep enjoying the conversation!\n"
    #             + "Cost of the plan: 5 Rs\n"
    #             + "Learn more about the plan details at:\nhttps://makechat.pythonanywhere.com/plan-details"
    #         )

    def plan_expired_on_standard_plan(self, user_obj):
        """
        This function will send the message to subscribe
        """
        OutgoingMessage().send(
            user_number=str(user_obj.username),
            response_message="Oops! It seems your plan expired, Subscribe now!\nCost of plan : 5rs\n"
            + "Learn more about the plan details at:\nhttps://makechat.pythonanywhere.com/plan-details",
        )
        return True

    def plan_expired_for_image_quota(self, user_obj):
        """
        THis function will send message for
        plan expired or image qota expired
        """
        OutgoingMessage().send(
            user_number=str(user_obj.username),
            response_message="Oops! It seems your plan expired or image quota reached limit, Subscribe now!\nCost of plan : 5rs\n"
            + "Learn more about the plan details at:\nhttps://makechat.pythonanywhere.com/plan-details",
        )
        return True

    def is_text_message_expired(self, data: dict, len_of_messages: int):
        """
        This function will check does this user is expired
        """
        plan_expires = data["customer"].plan_expires_at
        is_expired = timezone.now() > plan_expires
        plan = data["customer"].plan
        if plan == "Free" and len_of_messages > TEXT_CHAT_LIMIT_FOR_FREE:
            return self.send_limit_exceeded_on_free_plan(user_obj=data["user"])

        if (
            plan == "Standard"
            and is_expired
            and len_of_messages > TEXT_CHAT_LIMIT_FOR_FREE
        ):
            return self.plan_expired_on_standard_plan(user_obj=data["user"])
        return False

    def is_image_message_expired(self, data: dict, len_of_messages: int):
        """
        This function will check does this user is expired
        """
        plan_expires = data["customer"].plan_expires_at
        is_expired = timezone.now() > plan_expires
        plan = data["customer"].plan
        image_quota = data["customer"].image_quota
        customer_obj = data["customer"]
        if plan == "Free" and customer_obj.image_quota == 0:
            return self.send_limit_exceeded_on_free_plan(user_obj=data["user"])

        if plan == "Standard" and is_expired or image_quota == 0:
            return self.plan_expired_for_image_quota(user_obj=data["user"])
        return False

    def get_request_type(self, message_body: str):
        """
        This function will return the request type
        """
        striped_message = message_body.strip()
        striped_message = striped_message[0:6].lower()
        if striped_message == "image/":
            return "image"
        return "text"

    def get_old_messages(self, user_obj):
        """
        THis function gets the old messages
        """
        return DataRetriver().get_messages_by_user(user=user_obj)

    def filter_message_by_request_type(self, request_type: str, messages: list):
        """
        This function will filter the message by type
        """
        res = []
        for message in messages:
            if request_type == message.message_type:
                res.append(message)
        return res

    def filter_message_by_hrs(self, messages: list, hrs: int = 24):
        """
        This function will filter the messages by hrs
        """
        res = []
        now_time = timezone.now()
        for message in messages:
            time_difference = now_time - message.created_at
            if time_difference <= timedelta(hours=hrs):
                res.append(message)
        return res

    def reply_text_message(self, data):
        """
        reply for text message
        """
        DataRetriver().create_message(
            user=data["user"], content=data["content"], role="user"
        )
        old_messages = self.filter_message_by_request_type(
            request_type="text", messages=self.get_old_messages(user_obj=data["user"])
        )
        messages_within_time_frame = self.filter_message_by_hrs(
            messages=old_messages, hrs=24
        )
        print("-------------", messages_within_time_frame)
        if self.is_text_message_expired(
            data=data, len_of_messages=len(messages_within_time_frame)
        ):
            print("========plan expired====")
            return {}
        print("conversing with chatgpt====")
        response = ChatGpt().chat(
            messages=ChatGpt().form_conversations(user_messages=old_messages[0:10]),
        )
        DataRetriver().create_message(
            user=data["user"], content=response, role="system"
        )
        send_message = OutgoingMessage().send(
            user_number=str(data["user"].username), response_message=response
        )
        return send_message

    def reply_image_message(self, data):
        """
        reply with image
        """
        DataRetriver().create_message(
            user=data["user"],
            content=data["content"],
            role="user",
            message_type="image",
        )
        old_messages = self.filter_message_by_request_type(
            request_type="image", messages=self.get_old_messages(user_obj=data["user"])
        )
        messages_within_time_frame = self.filter_message_by_hrs(
            messages=old_messages, hrs=24
        )
        print("-------------", messages_within_time_frame)
        if self.is_image_message_expired(
            data=data, len_of_messages=len(messages_within_time_frame)
        ):
            print("========plan expired====")
            return {}
        response = (ChatGpt().generate_image(image_prompt=data["content"]),)
        customer_obj = data["customer"]
        customer_obj.image_quota = customer_obj.image_quota - 1
        customer_obj.save()
        send_message = OutgoingMessage().send(
            user_number=str(data["user"].username),
            response_message="Image",
            mediaurl=response,
        )
        return send_message

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
            user_name=user_name, create_new_if_not_exists=True
        )
        customer_plan = customer_obj.plan
        request_type = self.get_request_type(message_body=content)
        data = {
            "user": user_obj,
            "customer": customer_obj,
            "content": content,
            "request_type": "text",
        }
        if request_type == "image":
            data["request_type"] = "image"
            new_content = data["content"].replace("image/", "")
            data["content"] = new_content
            response = self.reply_image_message(data=data)
        if request_type == "text":
            data["request_type"] = "text"
            response = self.reply_text_message(data=data)
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
