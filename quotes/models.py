from django.db import models
from django.utils import timezone
from datetime import timedelta

class Quote(models.Model):
    author = models.CharField(max_length=200)     # e.g., "Naruto", "KentuckyJoles"
    message = models.TextField()                  # the actual quote
    created_at = models.DateTimeField(auto_now_add=True)

    def is_expired(self):
        return timezone.now() > self.created_at + timedelta(days=7)

    def __str__(self):
        return f"{self.author}: {self.message[:50]}..."
