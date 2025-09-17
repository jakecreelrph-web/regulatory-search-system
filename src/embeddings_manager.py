# src/embeddings_manager.py
import os
import json
import pickle
import numpy as np
from typing import List, Dict, Tuple
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import streamlit as st

class EmbeddingsManager:
    def __init__(self, config: dict):
        self.config = config
        self.model_name = config['embeddings']['model']
        self.chunk_size = config['embeddings']['chunk_size']
        self.chunk_overlap = config['embeddings']['chunk_overlap']
        
        # Load sentence transformer model
        self._load_model()
        
        # Document embeddings storage
        self.embeddings_path = "data/embeddings"
        os.makedirs(self.embeddings_path, exist_ok=True)
    
    @st.cache_resource
    def _load_model(_self):
        """Load the sentence transformer model"""
        return SentenceTransformer(_self.model_name)
    
    def chunk_text(self, text: str) -> List[str]:
        """Split text into overlapping chunks"""
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + self.chunk_size
            chunk = text[start:end]
            chunks.append(chunk)
            
            if end >= len(text):
                break
                
            start += self.chunk_size - self.chunk_overlap
        
        return chunks
    
    def generate_embeddings(self, texts: List[str]) -> np.ndarray:
        """Generate embeddings for a list of texts"""
        model = self._load_model()
        embeddings = model.encode(texts, convert_to_tensor=False)
        return embeddings
    
    def process_document_embeddings(self, document_data: Dict) -> Dict:
        """Process embeddings for a document"""
        doc_id = document_data['id']
        text = document_data['text']
        
        # Check if embeddings already exist
        embeddings_file = f"{self.embeddings_path}/{doc_id}_embeddings.pkl"
        
        if os.path.exists(embeddings_file):
            with open(embeddings_file, 'rb') as f:
                return pickle.load(f)
        
        # Generate chunks
        chunks = self.chunk_text(text)
        
        # Generate embeddings
        embeddings = self.generate_embeddings(chunks)
        
        # Prepare embeddings data
        embeddings_data = {
            "document_id": doc_id,
            "chunks": chunks,
            "embeddings": embeddings,
            "num_chunks": len(chunks),
            "embedding_model": self.model_name
        }
        
        # Save embeddings
        with open(embeddings_file, 'wb') as f:
            pickle.dump(embeddings_data, f)
        
        return embeddings_data
    
    def search_similar_chunks(self, query: str, top_k: int = 10) -> List[Dict]:
        """Search for similar text chunks across all documents"""
        # Generate query embedding
        query_embedding = self.generate_embeddings([query])[0]
        
        results = []
        
        # Load all document embeddings
        for embedding_file in os.listdir(self.embeddings_path):
            if not embedding_file.endswith('_embeddings.pkl'):
                continue
                
            doc_id = embedding_file.replace('_embeddings.pkl', '')
            
            try:
                # Load embeddings
                with open(f"{self.embeddings_path}/{embedding_file}", 'rb') as f:
                    embeddings_data = pickle.load(f)
                
                # Calculate similarities
                similarities = cosine_similarity(
                    [query_embedding], 
                    embeddings_data['embeddings']
                )[0]
                
                # Get top chunks for this document
                for i, similarity in enumerate(similarities):
                    if similarity > self.config['search']['similarity_threshold']:
                        results.append({
                            "document_id": doc_id,
                            "chunk_index": i,
                            "chunk_text": embeddings_data['chunks'][i],
                            "similarity": float(similarity)
                        })
            
            except Exception as e:
                st.error(f"Error processing embeddings for {doc_id}: {str(e)}")
                continue
        
        # Sort by similarity and return top results
        results.sort(key=lambda x: x['similarity'], reverse=True)
        return results[:top_k]