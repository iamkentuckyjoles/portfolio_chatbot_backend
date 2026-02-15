from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Quote
from .serializers import QuoteSerializer

@api_view(['GET'])
def latest_quotes(request):
    # Order by newest first
    qs = Quote.objects.order_by('-created_at')
    
    # Only return results once at least 60 exist
    if qs.count() < 60:
        return Response([])  # empty list until threshold reached
    
    # Limit to the latest 60 quotes
    quotes = qs[:60]
    serializer = QuoteSerializer(quotes, many=True)
    return Response(serializer.data)
