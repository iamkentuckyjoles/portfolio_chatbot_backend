from django.urls import path
from .views import latest_quotes

urlpatterns = [
    path("quotes/", latest_quotes, name="latest_quotes"),
]
