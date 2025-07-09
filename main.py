import os
import re
import ast
import unicodedata
from enum import Enum
import tiktoken
import fitz  # PyMuPDF
import docx
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables
load_dotenv()

# Configure Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)

app = FastAPI()

# --- Enum for Dropdowns ---
class Language(str, Enum):
    english = "English"
    japanese = "Japanese"

# --- File Text Extraction ---

def extract_text_from_file(file: UploadFile) -> str:
    filename = file.filename.lower()
    if filename.endswith(".txt"):
        return file.file.read().decode("utf-8")

    elif filename.endswith(".pdf"):
        try:
            pdf = fitz.open(stream=file.file.read(), filetype="pdf")
            text = "\n".join([page.get_text() for page in pdf])
            pdf.close()
            return text
        except Exception:
            raise HTTPException(status_code=400, detail="Failed to read PDF file.")

    elif filename.endswith(".docx"):
        try:
            doc = docx.Document(file.file)
            return "\n".join([para.text for para in doc.paragraphs])
        except Exception:
            raise HTTPException(status_code=400, detail="Failed to read DOCX file.")

    elif filename.endswith(".doc"):
        raise HTTPException(status_code=400, detail=".doc format is not supported. Please convert to .docx.")

    else:
        raise HTTPException(status_code=400, detail="Unsupported file format. Only .txt, .pdf, and .docx are allowed.")

# --- Helper Functions ---

def normalize_text(text: str) -> str:
    return unicodedata.normalize('NFKC', text)

def estimate_tokens(text: str, model_name: str = "models/gemini-2.5-flash") -> int:
    try:
        encoding = tiktoken.encoding_for_model(model_name)
    except KeyError:
        encoding = tiktoken.get_encoding("cl100k_base")
    return len(encoding.encode(text))

def translate_with_builtin_exclusion(text: str, source_language: str, target_language: str) -> tuple[str, int]:
    model = genai.GenerativeModel(model_name="models/gemini-2.5-flash")
    text = normalize_text(text)

    # Step 1: Identify non-translatable phrases
    prompt_extract = f"""
From the following {source_language} text, extract phrases that should NOT be translated.
These include company names, product names, library names, Katakana loanwords (for Japanese), and proper nouns.
Return ONLY a valid Python list of strings. No explanation or extra formatting.

Text:
---
{text}
---

List:
"""
    try:
        response_extract = model.generate_content(prompt_extract)
        match = re.search(r'\[.*?\]', response_extract.text, re.DOTALL)
        if match:
            non_translatables = ast.literal_eval(match.group(0))
        else:
            non_translatables = []
    except Exception as e:
        print(f"Error identifying non-translatables: {e}")
        non_translatables = []

    # Step 2: Estimate tokens for only the parts that will be translated
    reduced_text = text
    for phrase in non_translatables:
        reduced_text = reduced_text.replace(phrase, '')
    token_estimate = estimate_tokens(reduced_text)

    # Step 3: Translate
    prompt_translate = f"""
Translate the following {source_language} text to {target_language}.
Do NOT translate company names, product names, library names, Katakana loanwords (for Japanese), or proper nouns.
Preserve them as-is in the translation.

Text:
---
{text}
---

Translated text:
"""
    try:
        response = model.generate_content(prompt_translate)
        translated = response.text.strip()
        return translated, token_estimate
    except Exception as e:
        print(f"Error during translation with exclusion logic: {e}")
        return "Translation failed.", token_estimate

def translate_direct(text: str, source_language: str, target_language: str) -> tuple[str, int]:
    model = genai.GenerativeModel(model_name="models/gemini-2.5-flash")
    text = normalize_text(text)

    prompt = f"""
Translate the following {source_language} text to {target_language}.

Text:
---
{text}
---

Translated text:
"""
    token_estimate = estimate_tokens(text)
    try:
        response = model.generate_content(prompt)
        return response.text.strip(), token_estimate
    except Exception as e:
        print(f"Error during direct translation: {e}")
        return "Translation failed.", token_estimate

# --- API Endpoint ---

@app.post("/translate-document/")
async def translate_document(
    file: UploadFile = File(...),
    source_language: Language = Form(...),
    target_language: Language = Form(...)
):
    if source_language == target_language:
        raise HTTPException(status_code=400, detail="Source and target languages must be different.")

    text = extract_text_from_file(file)

    # Estimate direct translation
    direct_translation, tokens_direct = translate_direct(text, source_language.value, target_language.value)

    # Estimate translation with exclusion logic
    translated, tokens_exclusion = translate_with_builtin_exclusion(text, source_language.value, target_language.value)

    return {
        "original_filename": file.filename,
        "source_language": source_language.value,
        "target_language": target_language.value,
        "translated_content": translated,
        "token_usage": {
            "with_exclusion": tokens_exclusion,
            "without_exclusion": tokens_direct,
            "estimated_tokens_saved": tokens_direct - tokens_exclusion
        }
    }

@app.get("/models")
def list_models():
    models = genai.list_models()
    return [m.name for m in models if "generateContent" in m.supported_generation_methods]
