"""
    hold the data base
"""
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

# Create your models here.

class Orders(models.Model):
    """
        handle the order
    """
    ORDER_STATUS = (
        ("pending", "pending"),
        ("success", "success"),
        ("failed", "failed"),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    order_id = models.CharField(max_length=100)
    plan_id = models.CharField(max_length=100)
    status = models.CharField(max_length=20, choices=ORDER_STATUS)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return self.user.username

class Customer(models.Model):
    """
    hold the customer data
    """

    PLAN_CHOICES = (
        ("Free", "Free Plan"),
        ("Standard", "Standard Plan"),
        ("Premium", "Premium Plan"),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    plan = models.CharField(max_length=20, choices=PLAN_CHOICES)
    plan_expires_at = models.DateTimeField(default=timezone.now)

    def __str__(self) -> str:
        return self.user.username


class UserMessage(models.Model):
    """
    messages of the user
    """

    ROLE = (
        ("user", "User"),
        ("system", "System"),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE, default="user")
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return self.user.username


class InvitedUsers(models.Model):
    """
    This model is to store the invites
    """

    invite_from = models.ForeignKey(User, on_delete=models.CASCADE)
    invite_to = models.CharField(max_length=20)
    onboarded = models.BooleanField(default=False)
    invited_at = models.DateTimeField(default=timezone.now)
    onboarded_at = models.DateTimeField(default=timezone.now)

    def __str__(self) -> str:
        return self.invite_from.username


class ChatThread(models.Model):
    """
    chat thread
    """

    thread_id = models.CharField(max_length=100)
    first_person = models.ForeignKey(User, on_delete=models.CASCADE, related_name='first_person_threads')
    second_person = models.ForeignKey(User, on_delete=models.CASCADE, related_name='second_person_threads')
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self) -> str:
        return str(self.thread_id)


class ChatMessage(models.Model):
    """
    message
    """

    thread = models.ForeignKey(ChatThread, on_delete=models.CASCADE)
    sender = models.ForeignKey(User, on_delete=models.CASCADE,related_name='msg_sender')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='msg_receiver')
    message = models.CharField(max_length=200)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self) -> str:
        return str(self.created_at)
