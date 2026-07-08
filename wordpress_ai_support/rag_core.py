import os
from dotenv import load_dotenv
from langchain_community.document_loaders import TextLoader
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# Load environment variables (API Key)
load_dotenv()

# Configuration variables
DATA_PATH = "./data/bluewave_knowledge_base_V6.txt"
FAISS_PATH = "./vector_store"

def initialize_vector_db():
    """
    Loads text data, chunks it, and stores it in a local FAISS database.
    """
    print("Loading documents...")
    loader = TextLoader(DATA_PATH, encoding='utf-8')
    documents = loader.load()

    print("Splitting text into chunks...")
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=700, chunk_overlap=100)
    chunks = text_splitter.split_documents(documents)

    print("Generating Google embeddings and building FAISS database...")
    embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-2")
    
    vector_db = FAISS.from_documents(chunks, embeddings)
    vector_db.save_local(FAISS_PATH)
    
    print("Vector database initialized successfully.")

def get_chatbot_response(user_query: str) -> str:
    """
    Uses custom Native Query Expansion and advanced Prompt Engineering 
    to handle complex/comparative queries without relying on unstable external modules.
    """
    # 1. Load the existing vector database
    embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-2")
    vector_db = FAISS.load_local(FAISS_PATH, embeddings, allow_dangerous_deserialization=True)
    
    # 2. Setup the Gemini LLM
    llm = ChatGoogleGenerativeAI(model="gemini-3.5-flash", temperature=0.1)

    # ==========================================
    # STEP A: NATIVE QUERY EXPANSION
    # ==========================================
    expansion_prompt = f"""
    شما یک دستیار هوش مصنوعی هستید. سوال زیر را بررسی کنید.
    اگر سوال شامل مقایسه دو محصول است (مثلا تفاوت X و Y)، آن را به دو عبارت جستجوی ساده تفکیک کنید و فقط با کاما (,) جدا کنید.
    اگر سوال ساده است، فقط خود سوال را برگردانید. هیچ کلمه اضافه‌ای ننویسید.
    سوال: {user_query}
    """
    
    try:
        # Ask LLM to break down the query
        expanded_str = llm.invoke(expansion_prompt).content
        # Split by comma and clean up whitespace
        search_queries = [q.strip() for q in expanded_str.split(',')]
        # Always ensure the original query is included
        if user_query not in search_queries:
            search_queries.append(user_query)
    except Exception as e:
        print(f"Expansion failed, using default query: {e}")
        search_queries = [user_query]

    # ==========================================
    # STEP B: MANUAL MULTI-SEARCH & DEDUPLICATION
    # ==========================================
    retrieved_docs = []
    for q in search_queries:
        # Search the database for each sub-query
        docs = vector_db.similarity_search(q, k=2)
        retrieved_docs.extend(docs)
        
    # Extract text and remove exact duplicates using a Set
    unique_contents = list({doc.page_content for doc in retrieved_docs})
    formatted_context = "\n\n---\n\n".join(unique_contents)

    # ==========================================
    # STEP C: FINAL ANSWER GENERATION (CONSULTANT)
    # ==========================================
    system_prompt = (
        "تو یک مشاور فنی ارشد و مهندس فروش در شرکت BlueWave Robotics هستی.\n"
        "وظیفه تو پاسخ‌گویی دقیق، حرفه‌ای و دلسوزانه به مشتریان بر اساس اطلاعات ارائه شده است.\n\n"
        "دستورالعمل‌های حیاتی:\n"
        "۱. فقط و فقط از اطلاعات موجود در متن (Context) استفاده کن.\n"
        "۲. اگر کاربر تفاوت دو محصول را پرسید، اطلاعات هر دو را استخراج کن و به صورت یک مقایسه ساختاریافته (جدول یا لیست بولت‌دار) ارائه بده.\n"
        "۳. اگر کاربر برای شروع کار راهنمایی خواست، بهترین برد را بر اساس اطلاعات پیشنهاد بده و دلیل این انتخاب را بیان کن.\n"
        "۴. اگر سوال خارج از محصولات و حوزه رباتیک بود، محترمانه بگو که فقط در زمینه محصولات BlueWave تخصص داری.\n"
        "۵. هرگز مستقیماً نگو 'اطلاعات ندارم'؛ بلکه بگو 'با توجه به اطلاعات فعلی...' و بهترین حدس یا راهنمایی نزدیک را ارائه کن.\n\n"
        f"Context:\n{formatted_context}"
    )

    final_prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "{input}"),
    ])

    # Build simple LCEL chain
    rag_chain = final_prompt | llm | StrOutputParser()
    
    # Execute and return
    response = rag_chain.invoke({"input": user_query})
    return response

if __name__ == "__main__":
    # Build the database when running this file directly
    initialize_vector_db()