# STM32 MicroPython hardware assistant — backend

A RAG (Retrieval-Augmented Generation) backend that answers questions about a
custom STM32F405RGT6-based development board ("MicroBluePy") and helps users
write MicroPython code for it — pin usage, peripherals (UART/I2C/SPI/ADC/PWM),
and hardware safety warnings.

This backend is built for a **single client**: a Kotlin/Android app. All RAG
processing, the knowledge base, and the LLM calls (Gemini primary, Groq
fallback) live only on the server — the app is a thin HTTP client, by design
(see the architecture discussion that led to this decision: keeping API keys
and rate limiting centralized, so the app can scale to many users without any
client-side changes).

## Project structure

```
stm32_micropython_assistant/
├── main.py                    # FastAPI app — single /chat endpoint
├── core/
│   ├── rag_core.py             # RAG engine: chunking, retrieval, LLM fallback chain
│   ├── response_utils.py       # Extracts raw links from the model's answer
│   └── security.py             # API key check for the mobile endpoint
├── data/
│   ├── board_datasheet.md      # STM32F405 / MicroBluePy pinout + peripherals + warnings
│   └── company_info.md         # Placeholder — fill in company/product info later
├── scripts/
│   └── build_vector_db.py      # Rebuilds the FAISS index from everything in data/
├── clients/
│   └── android/
│       └── README.md           # Placeholder for the Kotlin app's networking code
├── API_CONTRACT.md             # Full request/response contract for the Android app
├── requirements.txt
├── .env.example
└── .gitignore
```

## Why the knowledge base is chunked by headers, not by character count

`board_datasheet.md` contains one large Markdown table (the full pinout) under
a single `##` heading. A generic "split every N characters" approach would cut
that table mid-row, and a query like "which pin is safe for I2C?" could end up
retrieving only half the table — which is actively dangerous here, since a
wrong or incomplete pin answer can damage the board.

`core/rag_core.py` instead splits by Markdown headers (`##` / `###`), so each
logical section — the whole pinout table, or the whole hardware warnings
section — stays as one intact chunk. See the comments in `rag_core.py` for
details.

## Language note

Code, comments, and this documentation are in English. The **system prompt**
and the **knowledge base content** are kept in **Persian**, since the mobile
app's end users are Persian-speaking. If you'd rather the assistant reply in
English, that's a one-line change in `SYSTEM_PROMPT_TEMPLATE` inside
`core/rag_core.py` — ask if you'd like that switched.

## Setup

```bash
git clone <this-repo>
cd stm32_micropython_assistant

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# fill in GOOGLE_API_KEY / GROQ_API_KEY / MOBILE_APP_API_KEY
```

Build the vector database (first run, and again whenever files in `data/`
change):

```bash
python3 scripts/build_vector_db.py
```

Run the server locally:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Test it without writing any Android code yet:

```bash
curl -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -H "X-App-Key: YOUR_MOBILE_APP_API_KEY" \
  -d '{"message": "پین‌های I2C کدومن؟"}'
```

Or open `http://127.0.0.1:8000/docs` for an interactive Swagger UI.

## Production deployment (with multiple workers, for scale)

```bash
nohup gunicorn main:app -k uvicorn.workers.UvicornWorker -w 4 --bind 127.0.0.1:8000 > output.log 2>&1 &
```

## Still to do before connecting the Android app

1. Fill in `data/company_info.md` with real company/product info, then
   re-run `scripts/build_vector_db.py`.
2. Manually test enough questions (see suggestions below) to be confident in
   answer quality and pin-safety accuracy.
3. Double-check the pinout table in `data/board_datasheet.md` against the
   original PDF datasheet — this file was AI-extracted and numeric data
   (pin numbers, voltages) should be verified by a human before it's trusted
   in production, especially since wrong pin info could damage hardware.
4. Once satisfied, follow `API_CONTRACT.md` to wire up the existing Kotlin
   app.

## Suggested manual test questions

- "پین‌های I2C کدومن؟" (tests table + peripheral section retrieval together)
- "کد بده تا LED آبی رو چشمک بزنم" (tests MicroPython code generation with the right pin label)
- "می‌تونم از X4 برای LED استفاده کنم؟" (tests motor pin conflict warning — X4 is shared with Motor1)
- "میکروکنترلر چند تا ADC داره؟" (tests a direct factual lookup)
- "چطور موتور رو فقط با USB روشن کنم؟" (tests that the safety warning is surfaced, not just answered literally)
