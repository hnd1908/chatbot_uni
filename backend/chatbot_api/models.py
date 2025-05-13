from django.db import models

class Conversation(models.Model):
    user_id = models.CharField(max_length=255, null=True, blank=True)
    conversation_index = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.pk:  
            last_conv = Conversation.objects.filter(user_id=self.user_id).order_by("-conversation_index").first()
            self.conversation_index = (last_conv.conversation_index + 1) if last_conv else 0

        super().save(*args, **kwargs)

    def __str__(self):
        return f"User {self.user_id} - Conversation {self.conversation_index} - {self.created_at.strftime('%Y-%m-%d %H:%M:%S')}"
    
class ChatMessage(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name="messages", null=True, blank=True)
    index = models.IntegerField(default=0)
    user_message = models.TextField()
    bot_response = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"User: {self.user_message}, Bot: {self.bot_response}"