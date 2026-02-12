from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Quote
from .serializers import QuoteSerializer

@api_view(['GET'])
def latest_quotes(request):
    quotes = Quote.objects.order_by('-created_at')[:100]
    serializer = QuoteSerializer(quotes, many=True)
    return Response(serializer.data)
