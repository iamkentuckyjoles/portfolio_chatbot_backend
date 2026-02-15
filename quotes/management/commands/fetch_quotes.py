import requests, json, re
from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from quotes.models import Quote

MODEL_NAME = "gemini-2.5-flash"

class Command(BaseCommand):
    help = "Fetch 5 quotes from Gemini and save to DB (keep rolling 7-day window)"

    def handle(self, *args, **kwargs):
        # Delete only expired quotes (>7 days old)
        Quote.objects.filter(
            created_at__lt=timezone.now() - timedelta(days=7)
        ).delete()

        batch_size = 5
        total_quotes = 0

        prompt = (
            f"Generate {batch_size} inspirational quotes. "
            "They should come from anime, manga, manhwa, or developer life themes. "
            "Return the result strictly as a valid JSON array. "
            "Each item must have: author, message. "
            "Do not include any text outside the JSON."
        )

        response = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL_NAME}:generateContent?key={settings.GEMINI_API_KEY}",
            json={"contents": [{"parts": [{"text": prompt}]}]},
        )

        data = response.json()
        text_response = (
            data.get("candidates", [{}])[0]
                .get("content", {})
                .get("parts", [{}])[0]
                .get("text", "")
        )

        if not text_response.strip():
            self.stderr.write("Gemini returned an empty response")
            return

        # 🔧 Sanitize Gemini output
        cleaned = text_response.strip()
        # Remove Markdown fences
        cleaned = re.sub(r"^```json|```$", "", cleaned, flags=re.MULTILINE).strip()
        # Remove stray "-" lines
        cleaned = re.sub(r"^\s*-\s*$", "", cleaned, flags=re.MULTILINE)
        # Remove trailing commas before closing braces/brackets
        cleaned = re.sub(r",\s*([\]}])", r"\1", cleaned)

        try:
            quotes = json.loads(cleaned)
            for q in quotes:
                Quote.objects.create(
                    author=q.get("author", "unknown"),
                    message=q.get("message", "")
                )
                total_quotes += 1
        except json.JSONDecodeError as e:
            self.stderr.write(f"Failed to parse JSON: {e}")
            self.stderr.write(f"Sanitized response:\n{cleaned}")
            return

        self.stdout.write(self.style.SUCCESS(f"Saved {total_quotes} quotes"))
