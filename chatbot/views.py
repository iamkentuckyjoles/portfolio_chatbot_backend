import requests
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.conf import settings
from django.core.cache import cache
from django.db.models import Q
from .models import KnowledgeItem
from .serializers import KnowledgeItemSerializer
from django.contrib.postgres.search import TrigramSimilarity
import langdetect  



# Custom Limits
RATE_LIMIT_PER_MINUTE = 20
RATE_LIMIT_PER_DAY = 10000
REPEAT_LIMIT_CONSECUTIVE = 5
REPEAT_LIMIT_TOTAL = 10

# Messages
FALLBACK_MESSAGE_MINUTE = "Rate limit exceeded: please wait a minute before trying again."
FALLBACK_MESSAGE_DAY = "Daily limit reached: the chatbot is unavailable until tomorrow."
FALLBACK_MESSAGE_REPEAT = "You’ve asked the same question too many times. Please try something different."
FALLBACK_MESSAGE_ERROR = "Sorry, Gemini API did not return a valid response."
FALLBACK_MESSAGE_NO_DB = "Sorry, I don’t have an answer for that in my knowledge base."

MODEL_NAME = "gemini-2.5-flash"



@api_view(['POST'])
def chatbot(request):
    user_message = request.data.get("message", "").strip()
    user_ip = get_client_ip(request)

    # Detect language
    try:
        detected_lang = langdetect.detect(user_message)
    except:
        detected_lang = "en"

    # Knowledge base check (fuzzy match with pg_trgm)
    matches = KnowledgeItem.objects.annotate(
        similarity=TrigramSimilarity('question', user_message.lower())
    ).filter(similarity__gt=0.1).order_by('-similarity')[:5]

    if matches.exists():
        serializer = KnowledgeItemSerializer(matches, many=True)
        qa_pairs = serializer.data

        qa_text = "\n".join(
            [f"Q: {item['question']}\nA: {item['answer']}" for item in qa_pairs]
        )

        # Adjust prompt based on language
        if detected_lang in ["tl", "ceb"]:  # tl = Tagalog, ceb = Cebuano/Bisaya
            language_instruction = (
                "Respond in the same language (Tagalog or Bisaya) "
                "using natural, conversational phrasing."
            )
        else:
            language_instruction = (
                "Respond in English, naturally and concisely."
            )

        response = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL_NAME}:generateContent?key={settings.GEMINI_API_KEY}",
            json={
                "contents": [
                    {"parts": [
                        {"text": (
                            f"The user asked: '{user_message}'.\n\n"
                            f"Here are possible Q/A pairs from the knowledge base:\n{qa_text}\n\n"
                            f"Choose the most relevant answer and respond in first person. "
                            f"{language_instruction} Do not mention the knowledge base or explain the source."
                        )}
                    ]}
                ]
            },
        )

        data = response.json()
        text_response = (
            data.get("candidates", [{}])[0]
                .get("content", {})
                .get("parts", [{}])[0]
                .get("text", FALLBACK_MESSAGE_ERROR)
        )
        return build_response(text_response)

    return build_response(FALLBACK_MESSAGE_NO_DB)


def build_response(text):
    return Response({"response": text})


def get_client_ip(request):
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0]
    return request.META.get("REMOTE_ADDR")
