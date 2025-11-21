import os
import json
import hashlib
from pathlib import Path

# Google Gen AI Import
try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = None

PROMPT_DIR = Path(__file__).parent / "prompts"
CACHE_DIR = Path("data/grader_cache")
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# Configuration
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
# Using Flash for speed/cost (Free tier compatible)
GEMINI_MODEL = "gemini-2.0-flash" 

def _load_prompt_template(rubric_name: str):
    p = PROMPT_DIR / f"{rubric_name}.txt"
    if not p.exists():
        raise FileNotFoundError(f"Prompt template not found: {p}")
    return p.read_text()

def _make_cache_key(rubric_name: str, prompt: str, response: str, expected: str):
    key = "|".join([rubric_name, prompt or "", str(response) or "", str(expected) or ""])
    return hashlib.sha256(key.encode("utf-8")).hexdigest()

def _call_gemini(prompt_text: str):
    """Calls Gemini with Native JSON enforcement."""
    if not genai:
        raise ImportError("Please install google-genai: pip install google-genai")
    if not GOOGLE_API_KEY:
        raise ValueError("GOOGLE_API_KEY environment variable is missing")

    client = genai.Client(api_key=GOOGLE_API_KEY)

    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt_text,
        config=types.GenerateContentConfig(
            response_mime_type="application/json", # <--- ADK Best Practice
            temperature=0.1
        )
    )
    
    # Parse the JSON response directly
    try:
        return json.loads(response.text)
    except json.JSONDecodeError:
        return {"score": 1, "notes": "JSON Parsing failed from model output"}

def grade(rubric_name: str, prompt: str, response: str, expected: str = ""):
    """
    Evaluates the input using Gemini.
    """
    key = _make_cache_key(rubric_name, prompt, response, expected)
    cache_path = CACHE_DIR / f"{key}.json"

    # Check Cache
    if cache_path.exists():
        return json.loads(cache_path.read_text())

    # Prepare Prompt
    template = _load_prompt_template(rubric_name)
    filled_prompt = template.replace("{{prompt}}", str(prompt)) \
                            .replace("{{response}}", str(response)) \
                            .replace("{{expected}}", str(expected)) \
                            .replace("{{expected_tool}}", str(expected))

    # Call Google AI
    try:
        result = _call_gemini(filled_prompt)
    except Exception as e:
        print(f"Error calling Gemini: {e}")
        result = {"score": 0, "notes": f"API Error: {str(e)}"}

    # Save to Cache
    cache_path.write_text(json.dumps(result))
    return result