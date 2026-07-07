import os
from dotenv import load_dotenv
from langchain_community.document_loaders import TextLoader
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate

# Load environment variables (API Key)
load_dotenv()

# Configuration variables
DATA_PATH = "./data/knowledge_base.txt"
FAISS_PATH = "./vector_store"

def initialize_vector_db():
    """
    Loads text data, chunks it, and stores it in a local FAISS database.
    Run this function once whenever knowledge_base.txt is updated.
    """
    print("Loading documents...")
    loader = TextLoader(DATA_PATH, encoding='utf-8')
    documents = loader.load()

    print("Splitting text into chunks...")
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks = text_splitter.split_documents(documents)

    print("Generating Google embeddings and building FAISS database...")
    # Using Google's embedding model
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
    
    vector_db = FAISS.from_documents(chunks, embeddings)
    vector_db.save_local(FAISS_PATH)
    
    print("Vector database initialized successfully.")

def get_chatbot_response(user_query: str) -> str:
    """
    Takes the user query, searches the FAISS DB, and returns the Gemini API response.
    """
    # 1. Load the existing vector database
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
    vector_db = FAISS.load_local(FAISS_PATH, embeddings, allow_dangerous_deserialization=True)
    
    # 2. Setup the Gemini LLM (gemini-1.5-flash is extremely fast and free-tier eligible)
    llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0.1)

    # 3. Define the system prompt
    system_prompt = (
        "You are a helpful customer support assistant for a website. "
        "Use the following retrieved context to answer the user's question in Persian (Farsi). "
        "If you don't know the answer or the answer is not in the context, "
        "just say: 'متاسفانه من اطلاعاتی در این زمینه ندارم. لطفا با شماره پشتیبانی تماس بگیرید.' "
        "Do not make up answers.\n\n"
        "Context:\n{context}"
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "{input}"),
    ])

    # 4. Create the RAG chain
    retriever = vector_db.as_retriever(search_kwargs={"k": 3})
    question_answer_chain = create_stuff_documents_chain(llm, prompt)
    rag_chain = create_retrieval_chain(retriever, question_answer_chain)

    # 5. Execute and get response
    response = rag_chain.invoke({"input": user_query})
    return response["answer"]

if __name__ == "__main__":
    # Build the database when running this file directly
    initialize_vector_db()