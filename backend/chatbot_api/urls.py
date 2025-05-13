from django.urls import path
from .views import conversation_handler, conversation_history, create_new_conversation

urlpatterns = [
    path("conversation/", conversation_handler, name="conversation_handler"),
    path("conversation/history/", conversation_history, name="conversation_history"),
    path("conversation/create_new_conversation/", create_new_conversation, name="create_new_conversation"),
]
