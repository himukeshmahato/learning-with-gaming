import os
import json
import time
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

# ─────────────────────────────────────────────
#  Available models registry
# ─────────────────────────────────────────────
GEMINI_MODELS = [
    {"id": "gemini-2.5-flash", "name": "Gemini 2.5 Flash", "provider": "gemini"},
    {"id": "gemini-2.0-flash", "name": "Gemini 2.0 Flash", "provider": "gemini"},
    {"id": "gemini-2.0-flash-lite", "name": "Gemini 2.0 Flash Lite", "provider": "gemini"},
]

GROQ_MODELS = [
    {"id": "llama-3.3-70b-versatile", "name": "Llama 3.3 70B", "provider": "groq"},
    {"id": "llama-3.1-8b-instant", "name": "Llama 3.1 8B Instant", "provider": "groq"},
    {"id": "gemma2-9b-it", "name": "Gemma 2 9B", "provider": "groq"},
]

ALL_MODELS = GEMINI_MODELS + GROQ_MODELS


def get_available_models():
    """Return list of models whose API keys are configured."""
    available = []
    if os.getenv("GEMINI_API_KEY"):
        available.extend(GEMINI_MODELS)
    if os.getenv("groq_api") or os.getenv("GROQ_API_KEY"):
        available.extend(GROQ_MODELS)
    return available


# ─────────────────────────────────────────────
#  Shared prompt builder
# ─────────────────────────────────────────────
def _build_prompt(text_chunk: str, number_of_questions: int) -> str:
    return f"""You are an educational quiz generator.
Generate exactly {number_of_questions} multiple-choice questions from the study note below.

RULES:
- Each question must have exactly 4 options labeled A, B, C, D.
- Exactly one option must be correct.
- Questions must be clear, educational, and directly based on the text.
- Return ONLY a valid JSON array, no extra text or markdown.

FORMAT (return as a JSON array):
[
  {{
    "question": "Question text here?",
    "options": {{"A": "...", "B": "...", "C": "...", "D": "..."}},
    "answer": "A"
  }}
]

STUDY NOTE:
{text_chunk}
"""


# ─────────────────────────────────────────────
#  Gemini provider — single model attempt
# ─────────────────────────────────────────────
def _try_gemini_model(model_id: str, prompt: str) -> list | None:
    """Try a single Gemini model. Returns list of questions or None."""
    try:
        from google import genai
        from google.genai import types
    except ImportError:
        print("DEBUG: google-genai not installed, skipping Gemini.")
        return None

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("DEBUG: [Gemini] GEMINI_API_KEY not found in .env — skipping.")
        return None
    client = genai.Client(api_key=api_key)

    full_model = f"models/{model_id}"
    retries = 2
    delay = 10

    while retries >= 0:
        try:
            print(f"DEBUG: [Gemini] Trying {full_model}...")
            response = client.models.generate_content(
                model=full_model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.3,
                ),
            )
            if response and response.text:
                data = json.loads(response.text)
                if isinstance(data, list) and len(data) > 0:
                    print(f"DEBUG: [Gemini] ✓ {len(data)} questions via {full_model}")
                    return data
            # Empty response
            return None

        except Exception as e:
            err = str(e)
            err_up = err.upper()

            if "QUOTA" in err_up or "limit: 0" in err:
                print(f"DEBUG: [Gemini] {full_model} quota exhausted")
                return None
            elif "429" in err_up or "EXHAUSTED" in err_up:
                if retries > 0:
                    print(f"DEBUG: [Gemini] {full_model} rate limited → retry in {delay}s ({retries} left)")
                    time.sleep(delay)
                    delay *= 2
                    retries -= 1
                else:
                    print(f"DEBUG: [Gemini] {full_model} rate limited, no retries left")
                    return None
            elif "404" in err_up or "NOT_FOUND" in err_up:
                print(f"DEBUG: [Gemini] {full_model} not found (404)")
                return None
            else:
                print(f"DEBUG: [Gemini] {full_model} error: {e}")
                return None

    return None


# ─────────────────────────────────────────────
#  Groq provider — single model attempt
# ─────────────────────────────────────────────
def _try_groq_model(model_id: str, prompt: str) -> list | None:
    """Try a single Groq model. Returns list of questions or None."""
    groq_key = os.getenv("groq_api") or os.getenv("GROQ_API_KEY")
    if not groq_key:
        print("DEBUG: [Groq] No groq_api key found in .env — cannot use Groq.")
        return None

    try:
        from groq import Groq
    except ImportError:
        print("DEBUG: [Groq] groq package not installed.")
        return None

    client = Groq(api_key=groq_key)

    try:
        print(f"DEBUG: [Groq] Trying {model_id}...")
        chat = client.chat.completions.create(
            model=model_id,
            messages=[
                {
                    "role": "system",
                    "content": "You are an educational quiz generator. Always respond with valid JSON only, no markdown.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            max_tokens=4096,
        )
        raw = chat.choices[0].message.content.strip()

        # Strip markdown code fences if present
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.strip()

        data = json.loads(raw)
        if isinstance(data, list) and len(data) > 0:
            print(f"DEBUG: [Groq] ✓ {len(data)} questions via {model_id}")
            return data

    except Exception as e:
        err_up = str(e).upper()
        if "429" in err_up or "RATE" in err_up:
            print(f"DEBUG: [Groq] {model_id} rate limited")
        else:
            print(f"DEBUG: [Groq] {model_id} error: {e}")

    return None


# ─────────────────────────────────────────────
#  Try a single model by ID (any provider)
# ─────────────────────────────────────────────
def _try_model(model_id: str, prompt: str) -> list | None:
    """Try a specific model by its ID. Returns list of questions or None."""
    # Find model info
    model_info = next((m for m in ALL_MODELS if m["id"] == model_id), None)
    if not model_info:
        print(f"DEBUG: Unknown model ID: {model_id}")
        return None

    if model_info["provider"] == "gemini":
        return _try_gemini_model(model_id, prompt)
    elif model_info["provider"] == "groq":
        return _try_groq_model(model_id, prompt)
    return None


# ─────────────────────────────────────────────
#  Public entry point
# ─────────────────────────────────────────────
def generate_questions_from_chunk(text_chunk: str, number_of_questions: int = 5, preferred_model: str = "auto") -> dict:
    """
    Generate questions from a text chunk.
    
    Args:
        text_chunk: The study text to generate questions from
        number_of_questions: How many questions to generate
        preferred_model: Model ID to try first, or "auto" for default order
    
    Returns:
        dict with keys:
            "questions": list of question dicts
            "model_used": str — the model ID that succeeded
            "fallback": bool — True if a different model was used than requested
            "message": str — user-facing status message
    """
    result = {"questions": [], "model_used": None, "fallback": False, "message": ""}

    if not text_chunk or not text_chunk.strip():
        print("DEBUG: Text chunk is empty.")
        result["message"] = "Text chunk was empty."
        return result

    prompt = _build_prompt(text_chunk, number_of_questions)
    available = get_available_models()
    available_ids = [m["id"] for m in available]

    # Build the ordered list of models to try
    if preferred_model and preferred_model != "auto":
        # User selected a specific model — try it first, then fallback to others
        models_to_try = [preferred_model] + [m_id for m_id in available_ids if m_id != preferred_model]
    else:
        # Auto mode — try all in default order
        models_to_try = available_ids

    for i, model_id in enumerate(models_to_try):
        questions = _try_model(model_id, prompt)
        if questions:
            is_fallback = (i > 0 and preferred_model != "auto")
            model_info = next((m for m in ALL_MODELS if m["id"] == model_id), None)
            model_name = model_info["name"] if model_info else model_id

            result["questions"] = questions
            result["model_used"] = model_id
            result["fallback"] = is_fallback

            if is_fallback:
                preferred_info = next((m for m in ALL_MODELS if m["id"] == preferred_model), None)
                preferred_name = preferred_info["name"] if preferred_info else preferred_model
                result["message"] = f"⚠️ {preferred_name} failed to respond. Auto-switched to {model_name}."
                print(f"DEBUG: Fallback! {preferred_model} → {model_id}")
            else:
                result["message"] = f"✅ Questions generated by {model_name}."

            return result

    result["message"] = "❌ All AI models failed. Please try again later."
    print("DEBUG: All AI providers failed or quota exhausted.")
    return result
