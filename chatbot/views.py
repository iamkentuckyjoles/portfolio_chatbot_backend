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
from .services.weather import get_weather, format_weather
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings


# Limits
RATE_LIMIT_PER_MINUTE = 5
RATE_LIMIT_PER_DAY = 20
REPEAT_LIMIT_TOTAL = 1
GLOBAL_DAILY_LIMIT = 100
PER_KEY_DAILY_LIMIT = 16   # per key daily cap

# Fallback messages
FALLBACK_MESSAGE_MINUTE = "You’re asking too quickly. Please wait a moment before trying again."
FALLBACK_MESSAGE_DAY = "You’ve reached today’s question limit. I’ll be available again tomorrow."
FALLBACK_MESSAGE_REPEAT = "You already asked me about that. Please try something different."
FALLBACK_MESSAGE_ERROR = "Sorry, I couldn’t process that request. Please try again."
FALLBACK_MESSAGE_NO_DB = "Sorry, I don’t have that knowledge yet. Please ask another question about me, my projects and experiences."
FALLBACK_MESSAGE_QUOTA = "I’m resting for now. Please come back later."
FALLBACK_MESSAGE_GLOBAL = "The daily limit has been reached. Please try again tomorrow."

MODEL_NAME = "gemini-2.5-flash"

API_KEYS = [
    settings.GEMINI_API_KEY_1,
    settings.GEMINI_API_KEY_2,
    settings.GEMINI_API_KEY_3,
    settings.GEMINI_API_KEY_4,
    settings.GEMINI_API_KEY_5,
    settings.GEMINI_API_KEY_6,
]


def get_global_usage():
    today = timezone.now().date()
    key = f"global_usage_{today}"
    used = cache.get(key, 0)
    return used, key


def increment_global_usage():
    used, key = get_global_usage()
    cache.set(key, used + 1, timeout=86400)
    return used + 1


def check_rate_limits(user_ip, user_message):
    """Check per-minute, per-day, and repeat question limits."""
    now = timezone.now()
    minute_key = f"rate_minute_{user_ip}_{now.strftime('%Y%m%d%H%M')}"
    day_key = f"rate_day_{user_ip}_{now.strftime('%Y%m%d')}"
    repeat_key = f"repeat_{user_ip}_{user_message.lower()}"

    # Per-minute
    minute_count = cache.get(minute_key, 0)
    if minute_count >= RATE_LIMIT_PER_MINUTE:
        return FALLBACK_MESSAGE_MINUTE
    cache.set(minute_key, minute_count + 1, timeout=60)

    # Per-day
    day_count = cache.get(day_key, 0)
    if day_count >= RATE_LIMIT_PER_DAY:
        return FALLBACK_MESSAGE_DAY
    cache.set(day_key, day_count + 1, timeout=86400)

    # Repeat question
    if cache.get(repeat_key):
        return FALLBACK_MESSAGE_REPEAT
    cache.set(repeat_key, True, timeout=86400)

    return None


@api_view(['POST'])
def chatbot(request):
    user_message = request.data.get("message", "").strip()
    user_ip = get_client_ip(request)

    # Rate limit checks
    limit_message = check_rate_limits(user_ip, user_message)
    if limit_message:
        used, _ = get_global_usage()
        return Response({"response": limit_message, "usage": f"{used}/{GLOBAL_DAILY_LIMIT}"})

    # Global usage check
    used, key = get_global_usage()
    if used >= GLOBAL_DAILY_LIMIT:
        return Response({"response": FALLBACK_MESSAGE_GLOBAL, "usage": f"{GLOBAL_DAILY_LIMIT}/{GLOBAL_DAILY_LIMIT}"})

    # Increment global usage
    current_usage = increment_global_usage()

    # Detect language
    try:
        detected_lang = langdetect.detect(user_message)
    except:
        detected_lang = "en"

    # Knowledge base check
    matches = KnowledgeItem.objects.annotate(
        similarity=TrigramSimilarity('question', user_message.lower())
    ).filter(similarity__gt=0.1).order_by('-similarity')[:5]

    if matches.exists():
        serializer = KnowledgeItemSerializer(matches, many=True)
        qa_pairs = serializer.data

        qa_text = "\n".join(
            [f"Q: {item['question']}\nA: {item['answer']}" for item in qa_pairs]
        )

        # Language instruction
        if detected_lang in ["tl", "ceb"]:
            language_instruction = "Respond in the same language (Tagalog or Bisaya) using natural, conversational phrasing."
        else:
            language_instruction = "Respond in English, naturally and concisely."

        # Prompt guardrails
        prompt_text = (
            f"The user asked: '{user_message}'.\n\n"
            f"Here are possible Q/A pairs from the knowledge base:\n{qa_text}\n\n"
            f"Answer directly as Kenth Lumantao, in first person. {language_instruction} "
            f"Always keep a friendly tone: greet the user when appropriate, thank them for asking, "
            f"and express pleasure or gratitude in your replies (for example: 'You're welcome,' 'I'm glad you asked,' "
            f"'It’s my pleasure to share,' etc.). "
            f"Never say 'As an AI' or mention lacking feelings or a body. "
            f"If you don’t know the answer, reply with: "
            f"'Sorry, I don’t have that knowledge yet. Please ask another question about me, my projects and experiences'"
        )

        # Try all API keys until one works
        text_response = FALLBACK_MESSAGE_ERROR
        for idx, api_key in enumerate(API_KEYS):
            usage_key = f"gemini_usage_{timezone.now().date()}_key{idx}"
            used_key = cache.get(usage_key, 0)
            if used_key >= PER_KEY_DAILY_LIMIT:
                continue  # skip exhausted key

            response = requests.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL_NAME}:generateContent?key={api_key}",
                json={"contents": [{"parts": [{"text": prompt_text}]}]},
            )

            if response.status_code == 200:
                data = response.json()
                text_response = (
                    data.get("candidates", [{}])[0]
                        .get("content", {})
                        .get("parts", [{}])[0]
                        .get("text", FALLBACK_MESSAGE_ERROR)
                )
                cache.set(usage_key, used_key + 1, timeout=86400)
                break
            elif response.status_code == 429:
                # mark this key as exhausted
                cache.set(usage_key, PER_KEY_DAILY_LIMIT, timeout=86400)
                continue
            else:
                continue

        # If no key worked
        if text_response == FALLBACK_MESSAGE_ERROR:
            return Response({"response": FALLBACK_MESSAGE_QUOTA, "usage": f"{current_usage}/{GLOBAL_DAILY_LIMIT}"})

        return Response({"response": text_response, "usage": f"{current_usage}/{GLOBAL_DAILY_LIMIT}"})

    return Response({"response": FALLBACK_MESSAGE_NO_DB, "usage": f"{current_usage}/{GLOBAL_DAILY_LIMIT}"})


def get_client_ip(request):
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0]
    return request.META.get("REMOTE_ADDR")


@api_view(["GET"])
def villaba_weather(request):
    raw_data = get_weather()
    formatted = format_weather(raw_data)
    return Response(formatted)

@api_view(["GET"])
def chatbot_usage(request):
    used, _ = get_global_usage()
    return Response({"usage": f"{used}/{GLOBAL_DAILY_LIMIT}"})

@api_view(["POST"])
def send_contact_email(request):
    token = request.data.get("recaptcha_token")
    recaptcha_result = verify_recaptcha(token, request.META.get("REMOTE_ADDR"))

    # ✅ Debug print to confirm backend verification 
    print("Recaptcha result:", recaptcha_result)

    if not recaptcha_result.get("success") or recaptcha_result.get("score", 0) < 0.5:
        return Response({"status": "failed", "message": "reCAPTCHA verification failed"}, status=400)

    # Proceed with sending email if reCAPTCHA passes
    name = request.data.get("name")
    email = request.data.get("email")
    message = request.data.get("message")

    subject = f"New message from {name}"
    body = f"Sender: {email}\n\nMessage:\n{message}"

    send_mail(
        subject,
        body,
        settings.EMAIL_HOST_USER,
        [settings.EMAIL_HOST_USER],
        fail_silently=False,
    )

    return Response({"status": "Message sent"})


def verify_recaptcha(token, remote_ip=None):
    url = "https://www.google.com/recaptcha/api/siteverify"
    data = {
        "secret": settings.RECAPTCHA_SECRET_KEY,
        "response": token,
    }
    if remote_ip:
        data["remoteip"] = remote_ip

    r = requests.post(url, data=data)
    return r.json()
