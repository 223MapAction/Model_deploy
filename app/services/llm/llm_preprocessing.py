import os
import streamlit as st
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferWindowMemory
from langchain_community.chat_models import ChatOpenAI
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.retrievers import ContextualCompressionRetriever
from langchain.retrievers.document_compressors import LLMChainExtractor
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader

@st.cache_resource
def chain_workflow(openai_api_key):
    """
    Initializes and configures a conversational retrieval chain with document understanding and storage capabilities.

    This function configures a complete workflow for a conversational AI system, including PDF document loading, 
    document splitting, embedding, and compression-based retrieval from a conversational context using LangChain 
    and OpenAI technologies. The setup involves creating a vector database if it doesn't exist, and utilizing it for 
    context retrieval in conversation.

    Args:
        openai_api_key (str): API key for OpenAI services, used for both embedding generation and conversational responses.

    Returns:
        ConversationalRetrievalChain: A configured LangChain conversational retrieval chain, ready for deploying in a chatbot system.
    """
    llm_name = "gpt-3.5-turbo"  # LLM model name for chat interactions

    # Directory to persist vector index
    persist_directory = os.environ.get('VECTOR_INDEX_PATH', 'vector_index/') 

    # Load OpenAI embedding model
    embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key)

    # Check if the vectorstore exists
    if not os.path.exists(os.environ.get("DB_PATH", "vector_index/chroma.sqlite3")):
        # Load and split documents if vectorstore does not exist
        file = os.environ.get("DOCUMENTS_PATH", "documents/DoniBara.pdf")
        loader = PyPDFLoader(file)
        documents = loader.load()

        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
        splits = text_splitter.split_documents(documents)

        vectordb = Chroma.from_documents(
            documents=splits,
            embedding=embeddings,
            persist_directory=persist_directory
        )

        vectordb.persist()
        print("Vectorstore created and saved successfully. The 'chroma.sqlite3' file has been created.")
    else:
        # Load existing vectorstore
        vectordb = Chroma(persist_directory=persist_directory, embedding_function=embeddings)

    # Load OpenAI chat model
    llm = ChatOpenAI(temperature=0.2, openai_api_key=openai_api_key)

    # Setup document compressor and retrieval system
    compressor = LLMChainExtractor.from_llm(llm)
    compression_retriever = ContextualCompressionRetriever(
        base_compressor=compressor,
        base_retriever=vectordb.as_retriever(search_type="mmr", search_kwargs={"k": 3})
    )

    # Setup conversation memory for retaining context
    memory = ConversationBufferWindowMemory(k=3, memory_key="chat_history")

    # Initialize the conversational retrieval chain
    qa = ConversationalRetrievalChain.from_llm(
        llm=ChatOpenAI(model_name=llm_name, temperature=0.2, openai_api_key=openai_api_key), 
        chain_type="map_reduce", 
        retriever=compression_retriever, 
        memory=memory,
        get_chat_history=lambda h: h,
        verbose=True
    )

    return qa
