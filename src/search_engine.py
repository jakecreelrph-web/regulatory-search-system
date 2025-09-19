# src/search_engine.py
import os
import json
from typing import List, Dict, Optional
from datetime import datetime
import pandas as pd
import streamlit as st
from anthropic import Anthropic

from .embeddings_manager import EmbeddingsManager

class SearchEngine:
    def __init__(self, config: dict):
        self.config = config
        self.embeddings_manager = EmbeddingsManager(config)
        self.client = Anthropic(api_key=st.secrets["CLAUDE_API_KEY"])
    
    def load_document_metadata(self, doc_id: str) -> Optional[Dict]:
        """Load document metadata from processed folder"""
        metadata_path = f"data/processed/{doc_id}.json"
        
        if not os.path.exists(metadata_path):
            return None
        
        try:
            with open(metadata_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            st.error(f"Error loading metadata for {doc_id}: {str(e)}")
            return None
    
    def search_documents(self, query: str, filters: Dict = None) -> List[Dict]:
        """Search documents using semantic similarity"""
        # Get similar chunks
        similar_chunks = self.embeddings_manager.search_similar_chunks(
            query, 
            top_k=self.config['search']['max_results'] * 3
        )
        
        # Group by document and get metadata
        document_results = {}
        
        for chunk in similar_chunks:
            doc_id = chunk['document_id']
            
            if doc_id not in document_results:
                metadata = self.load_document_metadata(doc_id)
                if metadata:
                    document_results[doc_id] = {
                        "document": metadata,
                        "best_similarity": chunk['similarity'],
                        "matching_chunks": [chunk],
                        "total_matches": 1
                    }
            else:
                document_results[doc_id]['matching_chunks'].append(chunk)
                document_results[doc_id]['total_matches'] += 1
                if chunk['similarity'] > document_results[doc_id]['best_similarity']:
                    document_results[doc_id]['best_similarity'] = chunk['similarity']
        
        # Apply filters if provided
        if filters:
            document_results = self._apply_filters(document_results, filters)
        
        # Convert to list and sort
        results = list(document_results.values())
        results.sort(key=lambda x: x['best_similarity'], reverse=True)
        
        return results[:self.config['search']['max_results']]
    
    def _apply_filters(self, results: Dict, filters: Dict) -> Dict:
        """Apply search filters"""
        filtered_results = {}
        
        for doc_id, result in results.items():
            document = result['document']
            include = True
            
            # Regulator filter
            if filters.get('regulator') and filters['regulator'] != 'All':
                if document['analysis']['regulator'].lower() != filters['regulator'].lower():
                    include = False
            
            # Document type filter
            if filters.get('document_type') and filters['document_type'] != 'All':
                if document['analysis']['document_type'].lower() != filters['document_type'].lower():
                    include = False
            
            # Date range filter
            if filters.get('date_from') or filters.get('date_to'):
                doc_date = document.get('upload_date')
                if doc_date:
                    doc_date = datetime.fromisoformat(doc_date.replace('Z', '+00:00')).date()
                    
                    if filters.get('date_from') and doc_date < filters['date_from']:
                        include = False
                    if filters.get('date_to') and doc_date > filters['date_to']:
                        include = False
            
            if include:
                filtered_results[doc_id] = result
        
        return filtered_results
    
    def generate_ai_summary(self, query: str, search_results: List[Dict]) -> str:
        """Generate AI summary of search results"""
        if not search_results:
            return "No relevant documents found for your query."
        
        # Prepare context from top results
        context = ""
        for i, result in enumerate(search_results[:5]):
            doc = result['document']
            context += f"\nDocument {i+1}: {doc['filename']}\n"
            context += f"Regulator: {doc['analysis']['regulator']}\n"
            context += f"Summary: {doc['analysis']['summary']}\n"
            context += f"Key Requirements: {', '.join(doc['analysis']['key_requirements'][:3])}\n"
            
            # Add best matching chunk
            best_chunk = result['matching_chunks'][0]
            context += f"Relevant excerpt: {best_chunk['chunk_text'][:300]}...\n"
            context += "-" * 50 + "\n"
        
        prompt = f"""
        Based on the following regulatory documents, provide a comprehensive answer to this query: "{query}"
        
        Available Documents:
        {context}
        
        Please provide:
        1. A direct answer to the query
        2. Key regulatory requirements that apply
        3. Which documents are most relevant
        4. Any important compliance considerations
        
        Keep the response concise but comprehensive.
        """
        
        try:
            response = self.client.messages.create(
                model=self.config['claude']['model'],
                max_tokens=self.config['claude']['max_tokens'],
                temperature=self.config['claude']['temperature'],
                messages=[{"role": "user", "content": prompt}]
            )
            
            return response.content[0].text
            
        except Exception as e:
            st.error(f"Error generating AI summary: {str(e)}")
            return "Error generating summary. Please review the search results directly."
    
    def get_system_stats(self) -> Dict:
        """Get system statistics"""
        stats = {
            "total_documents": 0,
            "total_chunks": 0,
            "regulators": set(),
            "document_types": set(),
            "last_update": None
        }
        
        # Count processed documents
        processed_dir = "data/processed"
        if os.path.exists(processed_dir):
            for file in os.listdir(processed_dir):
                if file.endswith('.json'):
                    try:
                        with open(f"{processed_dir}/{file}", 'r') as f:
                            doc = json.load(f)
                            stats["total_documents"] += 1
                            stats["regulators"].add(doc['analysis']['regulator'])
                            stats["document_types"].add(doc['analysis']['document_type'])
                            
                            # Track latest update
                            upload_date = datetime.fromisoformat(doc['upload_date'])
                            if not stats["last_update"] or upload_date > stats["last_update"]:
                                stats["last_update"] = upload_date
                    except:
                        continue
        
        # Count embeddings
        embeddings_dir = "data/embeddings"
        if os.path.exists(embeddings_dir):
            import pickle
            for file in os.listdir(embeddings_dir):
                if file.endswith('_embeddings.pkl'):
                    try:
                        with open(f"{embeddings_dir}/{file}", 'rb') as f:
                            embeddings_data = pickle.load(f)
                            stats["total_chunks"] += embeddings_data['num_chunks']
                    except:
                        continue
        
        # Convert sets to lists, filtering out None values
        stats["regulators"] = sorted([r for r in stats["regulators"] if r is not None])
        stats["document_types"] = sorted([d for d in stats["document_types"] if d is not None])
        
        return stats