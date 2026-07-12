import os
from dotenv import load_dotenv
from langchain_community.document_loaders import TextLoader
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# Load environment variables (API Keys)
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
    
    
def check_local_fast_answers(user_query: str):
    """
    بررسی سوال کاربر برای پاسخگویی سریع محلی و بدون نیاز به API
    """
    # یکسان‌سازی حروف برای جستجوی بهتر (ی و ک عربی به فارسی)
    query = user_query.lower().replace('ي', 'ی').replace('ك', 'ک')
    
    # بانک کلیدواژه‌ها و پاسخ‌های قطعی
    local_faqs = {
        ("سلام", "درود", "خسته نباشید", "وقت بخیر", "hi", "hello"): 
            "سلام! من دستیار هوشمند BlueWave Robotics هستم. چطور می‌توانم راهنمایی‌تان کنم؟",
            
        ("شماره تماس", "تلفن پشتیبانی", "شماره شرکت", "چطور تماس بگیرم", "تلفن شرکت"): 
            "شماره تماس پشتیبانی فنی و فروش ما: **09130912580** می‌باشد. (پاسخگویی در ساعات کاری)",
            
        ("لینک فروشگاه", "از کجا بخرم", "خرید برد", "لیست قیمت", "قیمت"): 
            "برای مشاهده محصولات، قیمت‌های به‌روز و ثبت سفارش، لطفاً به فروشگاه ما سر بزنید:\nhttps://bluewaverobotics.ir/shop",
            
        ("کانال تلگرام", "پیج اینستاگرام", "شبکه های اجتماعی", "ارتباط با ما"): 
            "شما می‌توانید از طریق فرم تماس با ما در سایت و یا شماره 09130912580 با ما در ارتباط باشید."
    }
    
    # بررسی می‌کنیم که آیا هیچ‌کدام از کلیدواژه‌ها در جمله کاربر وجود دارد یا خیر
    for keywords, answer in local_faqs.items():
        # اگر کاربر فقط نوشته باشد "سلام" یا جمله‌ای مثل "سلام شماره تماس چنده؟"
        if any(keyword in query for keyword in keywords):
            return f"**[⚡ پاسخ سریع سیستم]**\n\n{answer}"
            
    # اگر سوال پیچیده بود و در لیست بالا نبود، مقدار None برمی‌گرداند تا به سراغ هوش مصنوعی برود
    return None

def get_chatbot_response(user_query: str) -> str:
    """
    Handles user queries with local pre-filtering and an explicit Fallback mechanism.
    """
    # ==========================================
    # پیش‌فیلتر محلی
    # ==========================================
    fast_answer = check_local_fast_answers(user_query)
    if fast_answer:
        return fast_answer  

    # ==========================================
    # بارگذاری دیتابیس و مدل‌ها
    # ==========================================
    # در این بخش اگر کلیدها یا دیتابیس مشکل داشته باشند، ارور رخ می‌دهد
    embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-2")
    vector_db = FAISS.load_local(FAISS_PATH, embeddings, allow_dangerous_deserialization=True)
    
    primary_llm = ChatGoogleGenerativeAI(model="gemini-3.5-flash", temperature=0.1)
    fallback_llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.1)
    
    # ==========================================
    # STEP A: NATIVE QUERY EXPANSION
    # ==========================================
    expansion_prompt = f"""
    شما یک دستیار هوش مصنوعی هستید. سوال زیر را بررسی کنید.
    اگر سوال شامل مقایسه دو محصول است، آن را به دو عبارت جستجوی ساده تفکیک کنید و با کاما جدا کنید.
    اگر ساده است، فقط خود سوال را برگردانید.
    سوال: {user_query}
    """
    
    try:
        expanded_str = primary_llm.invoke(expansion_prompt).content
    except Exception as e:
        print(f"Gemini expansion failed: {e}")
        try:
            expanded_str = fallback_llm.invoke(expansion_prompt).content
        except Exception as fallback_e:
            print(f"Groq expansion failed: {fallback_e}")
            expanded_str = user_query

    search_queries = [q.strip() for q in expanded_str.split(',')]
    if user_query not in search_queries:
        search_queries.append(user_query)

    # ==========================================
    # STEP B: MANUAL MULTI-SEARCH & DEDUPLICATION
    # ==========================================
    try:
        retrieved_docs = []
        for q in search_queries:
            docs = vector_db.similarity_search(q, k=2)
            retrieved_docs.extend(docs)
            
        unique_contents = list({doc.page_content for doc in retrieved_docs})
        formatted_context = "\n\n---\n\n".join(unique_contents)
    except Exception as e:
        print(f"Vector search failed: {e}")
        return "متاسفانه ارتباط با پایگاه دانش موقتاً قطع شده است."

    # ==========================================
    # STEP C: FINAL ANSWER GENERATION (CONSULTANT)
    # ==========================================
    system_prompt = (
        "تو یک مشاور فنی ارشد و مهندس فروش در شرکت BlueWave Robotics هستی.\n"
        "وظیفه تو پاسخ‌گویی دقیق بر اساس اطلاعات ارائه شده است.\n"
        f"Context:\n{formatted_context}"
    )

    final_prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "{input}"),
    ])

    try:
        chain = final_prompt | primary_llm | StrOutputParser()
        response = chain.invoke({"input": user_query})
        return f"**[🤖 Responded by: Gemini 3.5]**\n\n{response}"
    except Exception as e:
        print(f"Gemini failed, switching to Groq: {e}")
        try:
            chain = final_prompt | fallback_llm | StrOutputParser()
            response = chain.invoke({"input": user_query})
            return f"**[⚡ Responded by: Groq (Llama 3)]**\n\n{response}"
        except Exception as fallback_e:
            print(f"All LLMs failed: {fallback_e}")
            return "سرورهای پردازش ابری در دسترس نیستند. پشتیبانی: 09130912580"
        

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

    # To identify which model generated the response for testing purposes:
    try:
        # Try Gemini first
        chain = final_prompt | primary_llm | StrOutputParser()
        response = chain.invoke({"input": user_query})
        # Add Gemini identifier
        return f"**[🤖 Responded by: Gemini 3.5]**\n\n{response}"
        
    except Exception as e:
        print(f"Gemini failed, switching to Groq: {e}")
        try:
            # Try Groq as fallback
            chain = final_prompt | fallback_llm | StrOutputParser()
            response = chain.invoke({"input": user_query})
            # Add Groq identifier
            return f"**[⚡ Responded by: Groq (Llama 3)]**\n\n{response}"
            
        except Exception as fallback_e:
            # Final layer of defense if both cloud servers fail
            print(f"All LLMs failed: {fallback_e}")
            return "سرورهای پردازش ابری در حال حاضر در دسترس نیستند. لطفاً در صورت نیاز به راهنمایی فوری با شماره پشتیبانی 09130912580 تماس بگیرید."

if __name__ == "__main__":
    # Rebuild the local vector DB
    initialize_vector_db()