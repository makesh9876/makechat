"""
    hold the data base
"""
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
# Create your models here.
USAGE_LIMIT_FOR_FREE=20

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
    usage_quota = models.IntegerField(default=USAGE_LIMIT_FOR_FREE)
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
    message_type = models.CharField(max_length=20, default="text")
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

class FreeAiRequests(models.Model):
    """
        KEEP Track of ai requests
    """
    requests_count = models.IntegerField(default=0)

    @classmethod
    def get_instance(cls):
        instance, _ = cls.objects.get_or_create(pk=1)
        return instance

    def save(self, *args, **kwargs):
        # Increment the counter before saving
        self.requests_count += 1
        super(FreeAiRequests, self).save(*args, **kwargs)