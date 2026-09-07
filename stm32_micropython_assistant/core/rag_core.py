"""
Core RAG (Retrieval-Augmented Generation) engine for the STM32 MicroPython
hardware assistant.

Domain: this assistant answers questions about a custom STM32F405RGT6-based
development board (product name: "MicroBluePy") and helps users write
MicroPython code for it (pin usage, peripherals, safety warnings, etc.).

Design notes (read this before editing):
- All knowledge base files live in ./data/*.md. Every .md file found there is
  loaded automatically — no code change needed when you add a new file.
  Currently: board_datasheet.md (pinout + electrical specs), company_info.md
  (company/product info, no code), library_reference.md (the BlueLib API
  surface — class names and methods, NOT full example programs), and
  sensor_reference.md (per-sensor electrical facts: voltage tolerance,
  protocol). See the project README for why library_reference.md and
  sensor_reference.md exist as separate files from company_info.md — an
  earlier version of this knowledge base accidentally dropped this content
  while filtering out full code samples and links, which caused the model
  to forget the BlueLib class API and hallucinate a wrong voltage warning.
- Chunking is done by Markdown headers (## and ###), NOT by a fixed character
  count. This matters a lot for this project specifically: the pinout table
  in board_datasheet.md is one long Markdown table under a single "##"
  header. If we split by character count (like a generic RAG project would),
  the table could be cut in the middle of a row, and the model would only
  "see" half the pin data for a query — which is dangerous when the answer
  involves telling a user which pin is safe to use.
- The end-user-facing language (system prompt content, and the knowledge
  base itself) is kept in Persian, matching the target audience of the
  mobile app. Only code and comments are in English.
"""

import os
from pathlib import Path

from dotenv import load_dotenv
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

load_dotenv()

DATA_DIR = "./data"
FAISS_PATH = "./vector_store"

# If a section (after splitting by ## / ###) is longer than this AND does not
# contain a Markdown table, it gets split further by character count.
# Sections that DO contain a table ("|" character present) are never split
# further, no matter how long, because cutting a table row in half is worse
# than having one large chunk.
MAX_CHUNK_CHARS_WITHOUT_TABLE = 1500

# System prompt is intentionally in Persian: this is what actually shapes the
# model's behavior and the language it replies in, and the target users of
# the mobile app are Persian-speaking makers/students.
SYSTEM_PROMPT_TEMPLATE = (
    "تو یک مهندس ارشد embedded systems و دستیار کدنویسی برای برد توسعه "
    "MicroBluePy (مبتنی بر تراشه STM32F405RGT6) هستی که با MicroPython "
    "برنامه‌نویسی می‌شه.\n\n"
    "دستورالعمل‌های حیاتی:\n"
    "۱. فقط و فقط از اطلاعات موجود در متن (Context) استفاده کن. اگه چیزی در "
    "Context نبود، حدس نزن؛ صریح بگو که این اطلاعات در دیتاشیت/مستندات فعلی "
    "مشخص نشده.\n"
    "۲. این برد از برچسب‌های سفارشی خودش روی سیلک‌اسکرین استفاده می‌کنه "
    "(مثل X1، Y9)، نه فقط نام پین میکروکنترلر (مثل PA0، PB10). همیشه در "
    "پاسخ و کدت از همون برچسب روی برد (X.../Y...) استفاده کن و نام پین "
    "میکروکنترلر رو در پرانتز بیار. مثال: Y9 (PB10).\n"
    "۳. قانون طلایی کدنویسی: قبل از نوشتن هر کدی، همیشه اول چک کن که آیا "
    "برای ماژول/سنسور درخواستی، یک کلاس اختصاصی در کتابخانه BlueLib (وارد "
    "شده با نام mb) در Context معرفی شده یا نه. اگه بود، حتماً کد رو با "
    "همون کلاس اختصاصی بنویس (مثلاً mb.BMotor، mb.BOled_Mbpy، mb.BRFID). "
    "فقط وقتی هیچ کلاس اختصاصی‌ای در Context برای اون ماژول پیدا نشد، از "
    "ماژول عمومی machine (مثل machine.Pin، machine.I2C) استفاده کن. کد رو "
    "همیشه داخل بلاک ```python``` برگردون.\n"
    "۴. قبل از نوشتن کد برای یک پین، حتماً چک کن که آیا اون پین با پین‌های "
    "موتور (Motor1 تا Motor4) یا کاربرد دیگه‌ای تداخل داره یا نه. اگه تداخل "
    "داشت، صریح هشدار بده و یک پین جایگزین از Context پیشنهاد بده.\n"
    "۵. اگه سوال دربردارنده نکات ایمنی سخت‌افزاری بود (ولتاژ، جریان، تحمل "
    "5V، BOOT0، تغذیه موتور)، همیشه هشدار مربوطه رو قبل از کد بیار، نه بعدش. "
    "این هشدار باید دقیقاً بر اساس مشخصات همون قطعه‌ی خاص در Context باشه، "
    "نه یک قانون کلی که از قطعه‌ی دیگه‌ای تعمیم دادی — مثلاً تحمل ولتاژ هر "
    "سنسور می‌تونه با تحمل ولتاژ پین‌های خود میکروکنترلر فرق داشته باشه.\n"
    "۶. اگه سوال کاملاً خارج از حوزه این برد و MicroPython بود، محترمانه "
    "بگو که فقط در همین زمینه تخصص داری.\n\n"
    "Context:\n{context}"
)


def _load_and_chunk_all_documents() -> list[Document]:
    """
    Reads every .md file in DATA_DIR and splits it by Markdown headers
    (## and ###) instead of by a fixed character count. This keeps each
    logical section (e.g. the whole pinout table, or the whole hardware
    warnings section) as one coherent chunk whenever possible.
    """
    headers_to_split_on = [("##", "section"), ("###", "subsection")]
    md_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on, strip_headers=False)
    fallback_splitter = RecursiveCharacterTextSplitter(
        chunk_size=MAX_CHUNK_CHARS_WITHOUT_TABLE, chunk_overlap=100
    )

    all_chunks: list[Document] = []
    data_dir = Path(DATA_DIR)

    for file_path in sorted(data_dir.glob("*.md")):
        text = file_path.read_text(encoding="utf-8")
        if not text.strip():
            # Skip empty/placeholder files (e.g. company_info.md before it's filled in)
            continue

        section_chunks = md_splitter.split_text(text)

        for chunk in section_chunks:
            has_table = "|" in chunk.page_content
            is_too_long = len(chunk.page_content) > MAX_CHUNK_CHARS_WITHOUT_TABLE

            if is_too_long and not has_table:
                # Only split further if there's no table to protect.
                for sub_doc in fallback_splitter.split_documents([chunk]):
                    sub_doc.metadata["source_file"] = file_path.name
                    all_chunks.append(sub_doc)
            else:
                chunk.metadata["source_file"] = file_path.name
                all_chunks.append(chunk)

    return all_chunks


def initialize_vector_db():
    """
    Builds (or rebuilds) the local FAISS vector database from every .md file
    in data/. Run this once initially, and again any time the knowledge base
    content changes (e.g. after filling in company_info.md).
    """
    print("Loading and chunking all markdown files in data/ ...")
    chunks = _load_and_chunk_all_documents()
    print(f"Total chunks created: {len(chunks)}")

    print("Generating Google embeddings and building FAISS database...")
    embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-2")
    vector_db = FAISS.from_documents(chunks, embeddings)
    vector_db.save_local(FAISS_PATH)

    print("Vector database initialized successfully.")


def check_local_fast_answers(user_query: str):
    """
    Local, LLM-free fast path for very common questions. Returns None if no
    match is found, in which case the caller falls through to the RAG+LLM
    pipeline.

    Note: only greetings are handled here for now. Once data/company_info.md
    is filled in, add company-specific FAQs (contact info, pricing, etc.)
    to this dict the same way.
    """
    query = user_query.lower().replace("ي", "ی").replace("ك", "ک")

    local_faqs = {
        ("سلام", "درود", "وقت بخیر", "hi", "hello"):
            "سلام! من دستیار فنی برد MicroBluePy هستم. می‌تونم درباره پین‌اوت، "
            "پریفرال‌ها، یا کدنویسی MicroPython کمکتون کنم.",
    }

    for keywords, answer in local_faqs.items():
        if any(keyword in query for keyword in keywords):
            return answer

    return None


def get_chatbot_response(user_query: str) -> dict:
    """
    Main entry point for the RAG pipeline. Returns a structured dict instead
    of a pre-formatted string, so main.py can shape the output however the
    mobile client needs it.

    Returns:
        {
            "text": str,            # raw Markdown answer (may include ```python ...``` code blocks)
            "model_used": str,      # "local_faq" | "gemini" | "groq" | "error"
            "is_fast_answer": bool  # True if it came from the local FAQ shortcut
        }
    """
    fast_answer = check_local_fast_answers(user_query)
    if fast_answer:
        return {"text": fast_answer, "model_used": "local_faq", "is_fast_answer": True}

    try:
        embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-2")
        vector_db = FAISS.load_local(FAISS_PATH, embeddings, allow_dangerous_deserialization=True)
        primary_llm = ChatGoogleGenerativeAI(model="gemini-3.5-flash", temperature=0.1)
        fallback_llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.1)
    except Exception as e:
        print(f"System initialization failed: {e}")
        return {
            "text": "متاسفانه در راه‌اندازی سیستم خطایی رخ داده است.",
            "model_used": "error",
            "is_fast_answer": False,
        }

    # k=6: many hardware questions need MULTIPLE sections at once — e.g.
    # "write code for the RFID module" needs the pinout table (which pins
    # are SPI), the library_reference.md entry (the BRFID class), AND the
    # sensor_reference.md entry (voltage tolerance) all at the same time.
    # Raising k from 4 to 6 was a direct fix for a real failure we saw:
    # with k=4, some queries only retrieved hardware chunks and never
    # reached the library/sensor reference chunks, causing the model to
    # either fall back to generic `machine` code or hallucinate safety
    # warnings not supported by the actual sensor's spec.
    try:
        retrieved_docs = vector_db.similarity_search(user_query, k=6)
        formatted_context = "\n\n---\n\n".join(doc.page_content for doc in retrieved_docs)
    except Exception as e:
        print(f"Vector search failed: {e}")
        return {
            "text": "متاسفانه ارتباط با پایگاه دانش موقتاً قطع شده است.",
            "model_used": "error",
            "is_fast_answer": False,
        }

    system_prompt = SYSTEM_PROMPT_TEMPLATE.format(context=formatted_context)
    final_prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "{input}"),
    ])

    try:
        chain = final_prompt | primary_llm | StrOutputParser()
        response = chain.invoke({"input": user_query})
        return {"text": response, "model_used": "gemini", "is_fast_answer": False}
    except Exception as e:
        print(f"Gemini failed, switching to Groq: {e}")
        try:
            chain = final_prompt | fallback_llm | StrOutputParser()
            response = chain.invoke({"input": user_query})
            return {"text": response, "model_used": "groq", "is_fast_answer": False}
        except Exception as fallback_e:
            print(f"All LLMs failed: {fallback_e}")
            return {
                "text": "سرورهای پردازش ابری در حال حاضر در دسترس نیستند. لطفاً بعداً دوباره تلاش کنید.",
                "model_used": "error",
                "is_fast_answer": False,
            }


if __name__ == "__main__":
    # Allows running `python3 core/rag_core.py` directly during development.
    initialize_vector_db()
