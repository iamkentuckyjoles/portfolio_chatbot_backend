import requests, json, re
from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from quotes.models import Quote

MODEL_NAME = "gemini-2.5-flash"

BATCH_SIZE = 5   # 5 quotes per run
KEEP_DAYS = 7     # delete quotes older than 7 days

class Command(BaseCommand):
    help = "Fetch 10 quotes per run (20 runs/day at midnight PH time), keep rolling 7-day window"

    def handle(self, *args, **kwargs):
        # 1. Delete expired quotes (>7 days old)
        expired = Quote.objects.filter(
            created_at__lt=timezone.now() - timedelta(days=KEEP_DAYS)
        )
        expired_count = expired.count()
        expired.delete()
        if expired_count:
            self.stdout.write(self.style.WARNING(f"Deleted {expired_count} expired quotes"))

        # 2. Build prompt for Gemini
        prompt = (
            f"Generate {BATCH_SIZE} inspirational quotes. "
            "They should focus on personal growth, success-driven mindset, "
            "self-confidence, perseverance, gratitude, and joy. "
            "Return the result strictly as a valid JSON array. "
            "Each item must have: author, message. "
            "Each quotes should be different from the latest 1-350 qoutes you have generated."
            "Do not include any text outside the JSON."
        )

        # 3. Call Gemini API
        response = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL_NAME}:generateContent?key={settings.GEMINI_API_KEY}",
            json={"contents": [{"parts": [{"text": prompt}]}]},
        )

        if response.status_code != 200:
            self.stderr.write(f"Gemini API error: {response.status_code} {response.text}")
            return

        try:
            data = response.json()
        except ValueError:
            self.stderr.write("Gemini returned non-JSON response")
            self.stderr.write(response.text)
            return

        text_response = (
            data.get("candidates", [{}])[0]
                .get("content", {})
                .get("parts", [{}])[0]
                .get("text", "")
        )

        if not text_response.strip():
            self.stderr.write("Gemini returned an empty response")
            return

        # 4. Sanitize Gemini output
        cleaned = text_response.strip()
        cleaned = re.sub(r"^```json|```$", "", cleaned, flags=re.MULTILINE).strip()
        cleaned = re.sub(r"^\s*-\s*$", "", cleaned, flags=re.MULTILINE)
        cleaned = re.sub(r",\s*([\]}])", r"\1", cleaned)

        # 5. Save quotes
        try:
            quotes = json.loads(cleaned)
            new_quotes = []
            for q in quotes:
                new_quotes.append(
                    Quote.objects.create(
                        author=q.get("author", "unknown"),
                        message=q.get("message", "")
                    )
                )
            self.stdout.write(self.style.SUCCESS(f"Saved {len(new_quotes)} quotes"))

            # Snapshot latest 50 for quick check
            latest_quotes = Quote.objects.order_by("-created_at")[:50]
            self.stdout.write(self.style.NOTICE("Latest quotes snapshot:"))
            for q in latest_quotes:
                self.stdout.write(f"{q.author}: {q.message}")

        except json.JSONDecodeError as e:
            self.stderr.write(f"Failed to parse JSON: {e}")
            self.stderr.write(f"Sanitized response:\n{cleaned}")
            return
