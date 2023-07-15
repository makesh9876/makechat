from django.contrib import admin
from .models import Customer, UserMessage, InvitedUsers, ChatMessage,ChatThread
# Register your models here.
admin.site.register(Customer)
admin.site.register(UserMessage)
admin.site.register(InvitedUsers)

admin.site.register(ChatThread)
admin.site.register(ChatMessage)
