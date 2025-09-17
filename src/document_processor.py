# src/document_processor.py
import os
import json
import hashlib
from datetime import datetime
from typing import Dict, List, Optional
import pandas as pd
from anthropic import Anthropic
import PyPDF2
from docx import Document
import streamlit as st

class DocumentProcessor:
    def __init__(self, config: dict):
        self.config = config
        self.client = Anthropic(api_key=st.secrets["CLAUDE_API_KEY"])
        
    def extract_text(self, file_path: str, file_type: str) -> str:
        """Extract text from various document types"""
        try:
            if file_type == 'pdf':
                return self._extract_from_pdf(file_path)
            elif file_type == 'docx':
                return self._extract_from_docx(file_path)
            elif file_type == 'txt':
                return self._extract_from_txt(file_path)
            else:
                raise ValueError(f"Unsupported file type: {file_type}")
        except Exception as e:
            st.error(f"Error extracting text from {file_path}: {str(e)}")
            return ""
    
    def _extract_from_pdf(self, file_path: str) -> str:
        """Extract text from PDF"""
        text = ""
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
        return text.strip()
    
    def _extract_from_docx(self, file_path: str) -> str:
        """Extract text from Word document"""
        doc = Document(file_path)
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        return text.strip()
    
    def _extract_from_txt(self, file_path: str) -> str:
        """Extract text from text file"""
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read().strip()
    
    def analyze_with_claude(self, text: str, filename: str) -> Dict:
        """Analyze document with Claude AI"""
        prompt = f"""
        Analyze this regulatory document and extract the following information:
        
        Document: {filename}
        Text: {text[:4000]}...
        
        Please provide a JSON response with:
        1. document_type: (regulation, guidance, notice, letter, etc.)
        2. regulator: (FDA, OSHA, EPA, etc.)
        3. subject_areas: [list of main topics]
        4. key_requirements: [list of key requirements or mandates]
        5. effective_date: (if mentioned)
        6. summary: (2-3 sentence summary)
        7. keywords: [relevant search keywords]
        
        Return only valid JSON.
        """
        
        try:
            response = self.client.messages.create(
                model=self.config['claude']['model'],
                max_tokens=self.config['claude']['max_tokens'],
                temperature=self.config['claude']['temperature'],
                messages=[{"role": "user", "content": prompt}]
            )
            
            result = json.loads(response.content[0].text)
            return result
            
        except Exception as e:
            st.error(f"Error analyzing document with Claude: {str(e)}")
            return {
                "document_type": "unknown",
                "regulator": "unknown",
                "subject_areas": [],
                "key_requirements": [],
                "effective_date": None,
                "summary": "Analysis failed",
                "keywords": []
            }
    
    def process_document(self, file_path: str, filename: str) -> Dict:
        """Complete document processing pipeline"""
        file_extension = filename.split('.')[-1].lower()
        
        # Extract text
        text = self.extract_text(file_path, file_extension)
        if not text:
            return None
        
        # Generate unique ID
        doc_id = hashlib.md5(f"{filename}{text[:100]}".encode()).hexdigest()
        
        # Analyze with Claude
        analysis = self.analyze_with_claude(text, filename)
        
        # Create document metadata
        document_data = {
            "id": doc_id,
            "filename": filename,
            "file_type": file_extension,
            "upload_date": datetime.now().isoformat(),
            "text": text,
            "analysis": analysis,
            "text_length": len(text),
            "processed": True
        }
        
        # Save to processed folder
        processed_path = f"data/processed/{doc_id}.json"
        os.makedirs("data/processed", exist_ok=True)
        
        with open(processed_path, 'w', encoding='utf-8') as f:
            json.dump(document_data, f, indent=2, ensure_ascii=False)
        
        return document_data