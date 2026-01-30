import chromadb
from chromadb.config import Settings
import uuid
from sentence_transformers import SentenceTransformer
import numpy as np

class VectorDB:
    def __init__(self, persist_directory="./chroma_db"):
        self.client = chromadb.PersistentClient(path=persist_directory)
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Collections for different data types
        self.resume_collection = self.client.get_or_create_collection("resumes")
        self.job_collection = self.client.get_or_create_collection("job_data")
    
    def add_resume(self, resume_text, metadata=None):
        """Add resume to vector database"""
        embeddings = self.model.encode([resume_text])
        doc_id = str(uuid.uuid4())
        
        self.resume_collection.add(
            embeddings=embeddings.tolist(),
            documents=[resume_text],
            metadatas=[metadata or {}],
            ids=[doc_id]
        )
        return doc_id
    
    def add_job_data(self, job_text, metadata=None):
        """Add job search data to vector database"""
        embeddings = self.model.encode([job_text])
        doc_id = str(uuid.uuid4())
        
        self.job_collection.add(
            embeddings=embeddings.tolist(),
            documents=[job_text],
            metadatas=[metadata or {}],
            ids=[doc_id]
        )
        return doc_id
    
    def search_similar_resume(self, query, n_results=3):
        """Search for similar resume content"""
        query_embedding = self.model.encode([query])
        
        results = self.resume_collection.query(
            query_embeddings=query_embedding.tolist(),
            n_results=n_results
        )
        return results
    
    def search_similar_jobs(self, query, n_results=5):
        """Search for similar job data"""
        query_embedding = self.model.encode([query])
        
        results = self.job_collection.query(
            query_embeddings=query_embedding.tolist(),
            n_results=n_results
        )
        return results