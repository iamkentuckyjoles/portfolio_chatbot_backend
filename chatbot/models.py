from django.db import models
from django.utils import timezone

class KnowledgeItem(models.Model):
    category = models.CharField(max_length=100)
    question = models.TextField()
    answer = models.TextField()
    uploaded_file_name = models.CharField(max_length=255, blank=True, null=True)
    custom_file_name = models.CharField(max_length=255, blank=True, null=True)
    uploaded_time = models.DateTimeField(default=timezone.now)


    def __str__(self):
        return f"{self.category}: {self.question[:50]}"
