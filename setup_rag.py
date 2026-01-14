from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, Settings
from llama_index.core.storage import StorageContext
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
import chromadb
import os

def setup_rag():
    """
    Set up RAG system with LlamaIndex and ChromaDB.
    Reads documents from bank_products folder and creates vector index.
    """
    print("Setting up RAG system...")
    
    
    print("Loading embedding model...")
    embed_model = HuggingFaceEmbedding(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )
    Settings.embed_model = embed_model
    
    
    print("Loading product documents...")
    documents = SimpleDirectoryReader("bank_products").load_data()
    print(f"Loaded {len(documents)} documents")
    
   
    print("Setting up vector database...")
    db_path = "./chroma_db"
    chroma_client = chromadb.PersistentClient(path=db_path)
    
    
    collection_name = "bank_products"
    try:
        chroma_client.delete_collection(collection_name)
    except:
        pass
    
    chroma_collection = chroma_client.create_collection(collection_name)
    
    
    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)
    
    
    print("Creating embeddings and index...")
    index = VectorStoreIndex.from_documents(
        documents,
        storage_context=storage_context,
        show_progress=True
    )
    
    print("✅ RAG system ready!")
    print(f"✅ Vector database stored in: {db_path}")
    print(f"✅ Collection: {collection_name}")
    
    return index

if __name__ == "__main__":
    setup_rag()