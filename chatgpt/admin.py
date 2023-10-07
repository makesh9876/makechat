from django.contrib import admin
from .models import (
    Customer, UserMessage, InvitedUsers,
    ChatMessage,ChatThread,FreeAiRequests,Quizes,
    QuotaReset
)
# Register your models here.
admin.site.register(Customer)
admin.site.register(UserMessage)
admin.site.register(InvitedUsers)

admin.site.register(ChatThread)
admin.site.register(ChatMessage)
admin.site.register(FreeAiRequests)
admin.site.register(Quizes)
admin.site.register(QuotaReset)