from rest_framework import serializers
from .models import KnowledgeItem

class KnowledgeItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = KnowledgeItem
        fields = ['id', 'category', 'question', 'answer']
