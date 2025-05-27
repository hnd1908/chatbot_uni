from django.urls import path
from .views import conversation_handler

urlpatterns = [
    path("conversation/", conversation_handler, name="conversation_handler"),
]
