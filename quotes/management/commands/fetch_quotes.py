import requests, json, re
from django.core.management.base import BaseCommand
from django.conf import settings
from quotes.models import Quote

MODEL_NAME = "gemini-2.5-flash"

class Command(BaseCommand):
    help = "Fetch 5 quotes from Gemini and save to DB"

    def handle(self, *args, **kwargs):
        # Delete expired quotes (>7 days old)
        Quote.objects.all().delete()

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

        # 🔧 Strip Markdown fences like ```json ... ```
        cleaned = re.sub(r"^```json|```$", "", text_response.strip(), flags=re.MULTILINE).strip()

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
            self.stderr.write(f"Raw response:\n{text_response}")
            return

        self.stdout.write(self.style.SUCCESS(f"Saved {total_quotes} quotes"))
