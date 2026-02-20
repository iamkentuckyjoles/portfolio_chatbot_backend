from django.urls import path
from .views import chatbot, villaba_weather, chatbot_usage, send_contact_email

urlpatterns = [
    path("chat/", chatbot, name="chatbot"),
    path("chat/usage/", chatbot_usage, name="chatbot_usage"),
    path("weather/villaba/", villaba_weather),
    path("send-email/", send_contact_email),
]
