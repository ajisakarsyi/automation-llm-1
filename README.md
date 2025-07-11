
# AI Document Translator

**Multilingual Document Translation with Gemini AI and Context-Aware Exclusions**

AI Document Translator is a FastAPI-based system that translates documents from English to Japanese and vice versa. It uses Google’s Gemini API and includes advanced logic to avoid translating terms such as product names, company names, and technical jargon.

## System Overview

### What is AI Document Translator?
AI Document Translator is a web-based application designed to extract text from `.pdf`, `.docx`, and `.txt` documents and intelligently translate the content while **preserving critical terminology** that should not be altered (e.g., Katakana, brand names, programming libraries).

### Key Features
- **Exclusion-Aware Translation**: Avoids translating technical names and phrases
- **Multi-Format Support**: Accepts `.pdf`, `.docx`, and `.txt`
- **Gemini AI Integration**: Uses Google’s large language model (Gemini 2.5 Flash)
- **RESTful API**: Easy integration via HTTP endpoints
- **Clean Output**: Returns structured JSON response with translated content

## Architecture

```
┌──────────────────────────────────────────────┐
│            AI Document Translator            │
├──────────────────────────────────────────────┤
│  FastAPI Application (main.py)               │
│  ├── Document Upload and Extraction          │
│  ├── Exclusion-Aware Translation Logic       │
│  └── Gemini API Integration                  │
├──────────────────────────────────────────────┤
│  Google Gemini LLM API                       │
└──────────────────────────────────────────────┘
```

## Project Structure

```
ai-document-translator/
├── main.py             # FastAPI app with translation logic
├── requirements.txt    # Python dependencies
├── openapi.yaml        # OpenAPI schema (optional)
├── test_JP.pdf         # Sample Japanese document
├── test_EN.pdf         # Sample English document
└── .env                # Environment configuration (not committed)
```

## Folder Structure Explanation

### Core Application Files
- **main.py**: FastAPI entry point containing route and business logic
- **requirements.txt**: All required packages including FastAPI, PyMuPDF, and Google Generative AI SDK

### Sample Files
- **test_JP.pdf / test_EN.pdf**: Demo documents for testing the translation pipeline

### Optional Files
- **openapi.yaml**: Custom OpenAPI schema (used for docs or client generation)

## Quick Start

### Prerequisites
- Python 3.10+
- Google Gemini API Key

### Installation

```bash
git clone <repository-url>
cd ai-document-translator

# Optional: Create and activate a virtual environment
python -m venv env
source env/bin/activate  # or `env\Scripts\activate` on Windows

# Install required packages
pip install -r requirements.txt
```

### Environment Setup

Create a `.env` file:

```bash
# .env
GEMINI_API_KEY=your_gemini_api_key_here
```

### Running the Server

```bash
uvicorn main:app --host localhost --port 8000 --reload
```

### API Usag

#### `POST /translate-document/`

Translate a document from English ↔ Japanese.

**Form Fields**:
- `file`: Upload `.pdf`, `.docx`, or `.txt`
- `source_language`: `English` or `Japanese`
- `target_language`: `English` or `Japanese`

**Sample cURL**:

```bash
curl -X POST "http://localhost:8000/translate-document/" \
  -F "file=@test_JP.pdf" \
  -F "source_language=Japanese" \
  -F "target_language=English"
```

#### `GET /models`

Returns the available Gemini models.
