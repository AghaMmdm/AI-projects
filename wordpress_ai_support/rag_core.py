import os
from dotenv import load_dotenv
from langchain_community.document_loaders import TextLoader
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
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
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks = text_splitter.split_documents(documents)

    print("Generating Google embeddings and building FAISS database...")
    # Fix: Changed to the latest Google embedding model (gemini-embedding-2)
    embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-2")
    
    vector_db = FAISS.from_documents(chunks, embeddings)
    vector_db.save_local(FAISS_PATH)
    
    print("Vector database initialized successfully.")

def format_docs(docs):
    """
    Utility function to format retrieved documents into a single string.
    """
    return "\n\n".join(doc.page_content for doc in docs)

def get_chatbot_response(user_query: str) -> str:
    """
    Takes the user query, searches the FAISS DB, and returns the Gemini API response
    using modern LCEL architecture.
    """
    # 1. Load the existing vector database
    # Fix: Changed to the latest Google embedding model
    embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-2")
    vector_db = FAISS.load_local(FAISS_PATH, embeddings, allow_dangerous_deserialization=True)
    
    # 2. Setup the Gemini LLM
    # Fix: Upgraded to Gemini 3.5 Flash (Older models like 1.5-flash are deprecated)
    llm = ChatGoogleGenerativeAI(model="gemini-3.5-flash", temperature=0.1)

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

    # 4. Create the retriever
    retriever = vector_db.as_retriever(search_kwargs={"k": 3})

    # 5. Build the RAG chain using LCEL
    rag_chain = (
        {"context": retriever | format_docs, "input": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )

    # 6. Execute and return the clean string response
    response = rag_chain.invoke(user_query)
    return response

if __name__ == "__main__":
    # Build the database when running this file directly
    initialize_vector_db()