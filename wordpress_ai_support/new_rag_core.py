import os
from dotenv import load_dotenv
from langchain_community.document_loaders import TextLoader
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# Load environment variables
load_dotenv()

# Configuration and paths
DATA_PATH = "./data/bluewave_knowledge_base_V6.txt"
FAISS_PATH = "./vector_store"

def initialize_vector_db():
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
    """Smart local fast response system"""
    query = user_query.lower().replace('ي', 'ی').replace('ك', 'ک')
    words = query.split()
    
    # 1. Check for greetings (only if the sentence is short)
    greetings = ["سلام", "درود", "خسته نباشید", "وقت بخیر", "hi"]
    if len(words) <= 3 and any(g in query for g in greetings):
        return "سلام! من دستیار هوشمند BlueWave Robotics هستم. چطور می‌توانم راهنمایی‌تان کنم؟"
    
    # 2. Check for exact keywords
    local_faqs = {
        ("شماره تماس", "تلفن", "پشتیبانی", "شماره شرکت"): 
            "شماره تماس پشتیبانی فنی و فروش ما: **09130912580** می‌باشد.",
        ("لینک", "فروشگاه", "خرید", "قیمت"): 
            "برای مشاهده محصولات و قیمت‌ها به فروشگاه ما سر بزنید:\nhttps://bluewaverobotics.ir/shop"
    }
    
    for keywords, answer in local_faqs.items():
        if any(keyword in query for keyword in keywords):
            return answer
            
    return None

def get_chatbot_response(user_query: str) -> str:
    # 1. Local pre-filtering
    fast_answer = check_local_fast_answers(user_query)
    if fast_answer:
        return fast_answer  

    # 2. Load database and models
    try:
        embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-2")
        vector_db = FAISS.load_local(FAISS_PATH, embeddings, allow_dangerous_deserialization=True)
        
        # Initialize primary and fallback LLMs
        primary_llm = ChatGoogleGenerativeAI(model="gemini-pro", temperature=0.1)
        fallback_llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.1)
    except Exception as e:
        return "متاسفانه در راه‌اندازی سیستم خطایی رخ داده است."

    # 3. Direct vector search
    try:
        docs = vector_db.similarity_search(user_query, k=3)
        formatted_context = "\n\n---\n\n".join([doc.page_content for doc in docs])
    except Exception as e:
        return "متاسفانه ترافیک سرور بالاست. لطفاً مجدداً تلاش کنید."

    # 4. Generate final response
    system_prompt = (
        "تو یک مشاور فنی ارشد و مهندس فروش در شرکت BlueWave Robotics هستی.\n"
        "وظیفه تو پاسخ‌گویی دقیق به مشتریان فقط بر اساس اطلاعات ارائه شده است.\n\n"
        f"Context:\n{formatted_context}"
    )

    final_prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "{input}"),
    ])

    # Execute primary model, fallback to secondary if it fails
    try:
        chain = final_prompt | primary_llm | StrOutputParser()
        response = chain.invoke({"input": user_query})
        return response
    except Exception as e:
        try:
            chain = final_prompt | fallback_llm | StrOutputParser()
            response = chain.invoke({"input": user_query})
            return response
        except Exception as fallback_e:
            return "سرورهای پردازش ابری در دسترس نیستند. پشتیبانی: 09130912580"