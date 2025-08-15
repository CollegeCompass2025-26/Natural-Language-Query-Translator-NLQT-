import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-pro")

if not API_KEY:
    raise RuntimeError("GEMINI_API_KEY is not set in .env")

# Configure the SDK once at import time
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel(MODEL_NAME,generation_config={"temperature": 0})


def generate_sql(prompt: str) -> str:
    # Basic call; you can add safety settings / system instructions if desired
    resp = model.generate_content(prompt)
    # Some SDK versions return resp.text; others have candidates; keep simple here
    sql = getattr(resp, "text", None)
    if not sql:
        # Fallback extraction if needed
        sql = "".join(p.text for p in resp.candidates[0].content.parts)
    return sql.strip()