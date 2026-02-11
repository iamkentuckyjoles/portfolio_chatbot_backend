# 🤖 Portfolio Chatbot AI (portfolio_chatbot_backend)

A Django REST Framework backend that combines a custom knowledge base (DB) with Gemini AI to deliver polished, context-aware chatbot responses. This repository is part of my portfolio and demonstrates how structured Q&A data and a generative model can be used together to produce natural, localized replies.

---

## ✨ Key Features
- Knowledge base stored in the database (model: `KnowledgeItem`).
  - Import Q&A data via Django Admin from CSV, TXT, or JSON.
  - Required import headers: `category`, `question`, `answer`.
- Gemini AI integration
  - Default model: `gemini-2.5-flash` (configurable via env).
  - Used to polish or generate answers when DB context is partial or missing.
  - Produces conversational responses in English, Tagalog, or Bisaya.
- Hybrid logic
  - Exact or fuzzy DB match → Gemini refines the DB answer.
  - No DB match → Gemini generates a natural response; falls back to a friendly fallback when appropriate.
- Language detection
  - Detects English/Tagalog/Bisaya and responds in the same language for natural conversation.
- Rate limiting
  - Per-minute and per-day limits plus protections against repeated identical questions (configurable).
- REST API
  - Endpoint to chat with the bot: `POST /api/chat/`

---

## 🛠 Tech Stack
- Backend: Django + Django REST Framework
- Database: PostgreSQL
- AI: Gemini (Google Generative Language) via API
- Cache: Django cache framework (used for rate limiting)
- Deployment: Docker + Docker Compose

---

## ⚙️ Configuration / Environment Variables

Create a `.env` file in the project root (example):

```env
# Django
DJANGO_SECRET_KEY=your_secret_key_here
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1

# Postgres
POSTGRES_DB=chatbot_db
POSTGRES_USER=chatbot_user
POSTGRES_PASSWORD=chatbot_pass
POSTGRES_HOST=db
POSTGRES_PORT=5432

# Gemini / AI
GEMINI_API_KEY=your_api_key_here


Adjust values as needed for production (set `DJANGO_DEBUG=False`, secure secret and DB credentials, and configure allowed hosts).

---

```
## 🚀 Quickstart (Docker)

1. Clone the repo

```
bash
git clone https://github.com/iamkentuckyjoles/portfolio_chatbot_backend.git
cd portfolio_chatbot_backend

```

2. Create `.env` using the example above.

3. Build and run with Docker Compose
```bash
docker-compose up --build -d
```
- The web service runs Django (container port 8000). Optionally the host port mapping may expose this on e.g. `8001` (check your `docker-compose.yml`).
- The db service runs PostgreSQL (container port 5432).

4. Apply migrations
```bash
docker-compose exec web python manage.py migrate
```

5. Create a superuser (for admin panel & imports)
```bash
docker-compose exec web python manage.py createsuperuser
```

6. (Optional) Load initial data or import via Django Admin:
- Visit `http://localhost:8001/admin/` (adjust host/port as mapped) and use the KnowledgeItem import feature to upload CSV/TXT/JSON. CSV must contain `category,question,answer` headers.

---

## 📡 API Usage

Endpoint
```
POST /api/chat/
Content-Type: application/json
```

Request example
```json
{ "message": "What is your name?" }
```

Response (DB fuzzy match + Gemini polish)
```json
{ "response": "My name is ken, nice to meet you!" }
```

Response (no DB match)
```json
{ "response": "Sorry, I don’t have an answer for that in my knowledge base." }
```

cURL example
```bash
curl -X POST http://localhost:8001/api/chat/ \
  -H "Content-Type: application/json" \
  -d '{"message":"What is your name?"}'
```

---

## 🧩 How it works (brief)
1. Incoming message is language-detected.
2. System searches the DB for exact or fuzzy matches (by question, category, or related keywords).
3. If a DB match exists:
   - The stored answer is optionally sent to Gemini for polishing (tone, grammar, localization).
   - The polished DB answer is returned in the detected language.
4. If no DB match:
   - Gemini is used to generate a natural reply.
   - If Gemini cannot provide a valid answer or is rate-limited, a friendly fallback message is returned.
5. Rate limiting is applied before AI calls to control costs and abuse.

---

## ✅ Admin CSV/JSON/TXT Import format
- Required columns (CSV/JSON entries / TXT lines mapped by admin parser):
  - category
  - question
  - answer

Example CSV:
```csv
category,question,answer
General,What is your name?,My name is Ken.
Support,How do I reset my password?,You can reset your password by...
```

---

## 🔒 Rate Limits & Safety
- Per-minute and per-day rate limits are enforced using Django cache 
- Repeat-question protections to prevent spam or accidental loops.
- Configure limits via environment variables in `.env`.

---

## 🧪 Testing & Local Development (without Docker)
- Create a Python virtualenv, install dependencies from `requirements.txt`.
- Configure a local Postgres or SQLite for quick tests (update `DATABASES` in Django settings).
- Export environment variables locally and run:
```bash
python manage.py migrate
python manage.py runserver 8000
```

---

## 📚 Extending & Notes
- Model choice and Gemini config are environment-driven (`MODEL_NAME`).
- You can extend language support by updating the language-detection logic and prompt templates.
- Consider caching frequent responses to reduce AI calls and costs.

---

## Contributing
- Open an issue or PR with improvements, bug fixes, or new import formats.
- Ensure new features include tests and update documentation as needed.

---


## Pls leave a like if this was helpful for you, thanks!



