from chromadb import PersistentClient
from sentence_transformers import SentenceTransformer
from src.config import settings
from typing import List, Dict
import os

class VectorStore:
    def __init__(self):
        os.makedirs(settings.vector_db_path, exist_ok=True)
        self.client = PersistentClient(path=settings.vector_db_path)
        self.embedding_model = SentenceTransformer(settings.embedding_model)
        self.collection = self._get_or_create_collection()
    
    def _get_or_create_collection(self):
        try:
            return self.client.get_collection("research_docs")
        except:
            return self.client.create_collection("research_docs")
    
    def add_documents(self, texts: List[str], metadatas: List[Dict]):
        ids = [f"doc_{i}" for i in range(len(texts))]
        embeddings = self.embedding_model.encode(texts).tolist()
        self.collection.add(ids=ids, embeddings=embeddings, documents=texts, metadatas=metadatas)
    
    def search(self, query: str, top_k: int = 5) -> List[Dict]:
        query_embedding = self.embedding_model.encode([query]).tolist()
        results = self.collection.query(query_embeddings=query_embedding, n_results=top_k)
        sources = []
        if results['documents'][0]:
            for i, doc in enumerate(results['documents'][0]):
                sources.append({
                    "content": doc,
                    "metadata": results['metadatas'][0][i] if results['metadatas'] else {}
                })
        return sources

vector_store = VectorStore()