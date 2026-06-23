# 🎮 QuizFall - AI-Powered PDF Learning Game

## 📌 Project Overview

QuizFall converts your PDF study notes into a falling-answer game powered by **Google Gemini AI**.  
Upload a PDF → AI generates MCQs → Catch the correct answer before it falls!

**Tech Stack**: Django 6.0.6 | Phaser.js | Google Gemini AI | SQLite | PyMuPDF

---

## 📁 Project Structure

```
testing/
├── .venv/                          # Virtual Environment (Python 3.14)
└── learning_with_gaming/           # Django Project Root
    ├── manage.py                   # Django management script
    ├── db.sqlite3                  # SQLite database
    ├── quizfall/                   # Project settings & URLs
    │   ├── settings.py
    │   ├── urls.py
    │   └── wsgi.py
    ├── quiz/                       # Quiz app (PDF upload, AI generation, auth)
    │   ├── views.py
    │   ├── models.py
    │   ├── ai_generator.py         # Gemini AI question generator
    │   ├── utils.py                # PDF text extraction & chunking
    │   └── forms.py
    ├── game/                       # Game app (Phaser engine, scoring, dashboard)
    │   ├── views.py
    │   ├── models.py
    │   └── urls.py
    ├── static/
    │   ├── css/style.css           # Global styles
    │   └── js/game.js              # Phaser.js game engine
    ├── templates/
    │   ├── base.html
    │   ├── quiz/upload.html
    │   ├── game/play.html          # Game lobby + Phaser canvas
    │   ├── game/result.html
    │   └── registration/           # Login & Register pages
    └── media/uploaded_pdfs/        # User-uploaded PDFs
```

---

## 🚀 How to Run the Server

### Step 1: Open Terminal in the Project Directory

```powershell
cd c:\Users\mukes\all\others\codes\testing\learning_with_gaming
```

### Step 2: Activate Virtual Environment

```powershell
..\.venv\Scripts\Activate
```

> After activation, you should see `(.venv)` at the beginning of your terminal prompt.

### Step 3: Run Database Migrations (first time only)

```powershell
..\.venv\Scripts\python manage.py migrate
```

### Step 4: Start the Development Server

```powershell
..\.venv\Scripts\python manage.py runserver
```

> The server will start at: **http://127.0.0.1:8000/**

### Step 5: Open in Browser

Navigate to: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)

---

## 🛑 How to Stop the Server

Press **`Ctrl + C`** in the terminal where the server is running.

> This sends an interrupt signal to Django and gracefully shuts down the server.

---

## 🔁 Quick Reference Commands

| Action | Command |
|---|---|
| **Navigate to project** | `cd c:\Users\mukes\all\others\codes\testing\learning_with_gaming` |
| **Activate venv** | `..\.venv\Scripts\Activate` |
| **Run server** | `..\.venv\Scripts\python manage.py runserver` |
| **Stop server** | `Ctrl + C` |
| **Run migrations** | `..\.venv\Scripts\python manage.py migrate` |
| **Create superuser** | `..\.venv\Scripts\python manage.py createsuperuser` |
| **Access admin panel** | `http://127.0.0.1:8000/admin/` |
| **Install dependencies** | `..\.venv\Scripts\pip install -r requirements.txt` |

---

## 📦 Installed Dependencies

| Package | Version | Purpose |
|---|---|---|
| Django | 6.0.6 | Web framework |
| google-genai | 2.9.0 | Gemini AI SDK for question generation |
| PyMuPDF | 1.27.2.3 | PDF text extraction |
| matplotlib | 3.11.0 | Dashboard chart generation |
| pillow | 12.2.0 | Image processing |
| pydantic | 2.13.4 | Data validation |
| requests | 2.34.2 | HTTP requests |

---

## 🔑 API Key Configuration

The Gemini API key is configured in:

```
quiz/ai_generator.py → get_gemini_client()
```

To change or set the key via environment variable:

```powershell
$env:GEMINI_API_KEY = "your-api-key-here"
```

> ⚠️ If you see "AI failed to generate questions" error, your API key may have hit its **rate limit (429)**. Wait ~60 seconds and try again.

---

## 🌐 App Routes

| URL | Description |
|---|---|
| `/` | Home page |
| `/quiz/upload/` | Upload PDF & generate quiz |
| `/quiz/login/` | Login page |
| `/quiz/register/` | Registration page |
| `/game/play/<id>/` | Game lobby + play |
| `/game/result/<id>/` | Game results & review |
| `/game/dashboard/` | Progress dashboard & charts |
| `/admin/` | Django admin panel |

---

## 🎮 Game Features

- **Configurable Lives**: 3, 5, or 7 lives per game
- **Adjustable Speed**: From "Snail's Pace" (0.005x) to "Turbo" (2.0x)
- **Question Count**: Choose how many questions per game
- **Touch Support**: Works on mobile with tap controls
- **Progress Tracking**: Dashboard with test-by-test analytics

---

## 🐛 Troubleshooting

| Problem | Solution |
|---|---|
| `ModuleNotFoundError: No module named 'django'` | Activate the venv first: `..\.venv\Scripts\Activate` |
| "AI failed to generate questions" | API rate limit hit. Wait 60s and retry |
| Server already running on port 8000 | Stop the other instance with `Ctrl+C`, or use `..\.venv\Scripts\python manage.py runserver 8001` |
| Database errors after model changes | Run `..\.venv\Scripts\python manage.py makemigrations` then `..\.venv\Scripts\python manage.py migrate` |
