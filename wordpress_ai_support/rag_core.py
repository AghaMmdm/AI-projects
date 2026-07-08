import os
from dotenv import load_dotenv
from langchain_community.document_loaders import TextLoader
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain.retrievers.multi_query import MultiQueryRetriever # Added for Query Expansion

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
    # Slightly increased chunk size helps retain context for comparative questions
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=700, chunk_overlap=100)
    chunks = text_splitter.split_documents(documents)

    print("Generating Google embeddings and building FAISS database...")
    embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-2")
    
    vector_db = FAISS.from_documents(chunks, embeddings)
    vector_db.save_local(FAISS_PATH)
    
    print("Vector database initialized successfully.")

def format_docs(docs):
    """
    Utility function to format retrieved documents into a single string.
    Filters out exact duplicates to keep the LLM context clean and efficient.
    """
    # Use a set to automatically drop duplicate text chunks found by the MultiQueryRetriever
    unique_docs = list({doc.page_content for doc in docs})
    return "\n\n---\n\n".join(unique_docs)

def get_chatbot_response(user_query: str) -> str:
    """
    Takes the user query, generates sub-queries for better retrieval (Query Expansion),
    searches the FAISS DB, and returns the Gemini API response acting as a Technical Consultant.
    """
    # 1. Load the existing vector database
    embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-2")
    vector_db = FAISS.load_local(FAISS_PATH, embeddings, allow_dangerous_deserialization=True)
    
    # 2. Setup the Gemini LLM
    llm = ChatGoogleGenerativeAI(model="gemini-3.5-flash", temperature=0.1)

    # 3. Define the advanced System Prompt (Consultant Persona)
    system_prompt = (
        "تو یک مشاور فنی ارشد و مهندس فروش در شرکت BlueWave Robotics هستی.\n"
        "وظیفه تو پاسخ‌گویی دقیق، حرفه‌ای و دلسوزانه به مشتریان بر اساس اطلاعات ارائه شده است.\n\n"
        "دستورالعمل‌های حیاتی:\n"
        "۱. فقط و فقط از اطلاعات موجود در متن (Context) استفاده کن.\n"
        "۲. اگر کاربر تفاوت دو محصول را پرسید، اطلاعات هر دو را استخراج کن و به صورت یک مقایسه ساختاریافته (جدول یا لیست بولت‌دار) همراه با نتیجه‌گیری ارائه بده.\n"
        "۳. اگر کاربر برای شروع کار راهنمایی خواست، بهترین برد را بر اساس اطلاعات پیشنهاد بده و دلیل این انتخاب را بیان کن.\n"
        "۴. اگر سوال خارج از محصولات و حوزه رباتیک بود، محترمانه بگو که فقط در زمینه محصولات BlueWave تخصص داری.\n"
        "۵. هرگز مستقیماً نگو 'اطلاعات ندارم'؛ بلکه بگو 'با توجه به اطلاعات فعلی...' و بهترین حدس یا راهنمایی نزدیک را ارائه کن.\n\n"
        "Context:\n{context}"
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "{input}"),
    ])

    # 4. Create the base retriever
    base_retriever = vector_db.as_retriever(search_kwargs={"k": 3})

    # 5. Apply Query Expansion using LangChain's MultiQueryRetriever
    # This automatically asks the LLM to break down comparative questions into simpler background searches
    advanced_retriever = MultiQueryRetriever.from_llm(
        retriever=base_retriever,
        llm=llm
    )

    # 6. Build the RAG chain using LCEL
    rag_chain = (
        {"context": advanced_retriever | format_docs, "input": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )

    # 7. Execute and return the clean string response
    response = rag_chain.invoke(user_query)
    return response

if __name__ == "__main__":
    # Build the database when running this file directly
    initialize_vector_db()