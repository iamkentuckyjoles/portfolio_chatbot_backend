from django.urls import path
from .views import chatbot
from .views import villaba_weather

urlpatterns = [
    path("chat/", chatbot, name="chatbot"),
    path("weather/villaba/", villaba_weather),
]
