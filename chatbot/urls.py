from django.urls import path
from .views import get_response

urlpatterns = [
    path('chatbot/', get_response),
]