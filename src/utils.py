# src/utils.py
import os
import yaml
import streamlit as st
from typing import Dict

@st.cache_data
def load_config() -> Dict:
    """Load system configuration"""
    with open('config.yaml', 'r') as f:
        return yaml.safe_load(f)

def setup_page_config():
    """Configure Streamlit page settings"""
    st.set_page_config(
        page_title="Regulatory Document Search",
        page_icon="📋",
        layout="wide",
        initial_sidebar_state="expanded"
    )

def authenticate_user(config: Dict) -> bool:
    """Simple password authentication"""
    if not config['authentication']['enable']:
        return True
    
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    
    if not st.session_state.authenticated:
        st.title("🔐 Authentication Required")
        password = st.text_input("Enter password:", type="password")
        
        if st.button("Login"):
            if password == config['authentication']['default_password']:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Incorrect password")
        
        st.stop()
    
    return True

def display_sidebar_info(config: Dict):
    """Display system information in sidebar"""
    st.sidebar.markdown("---")
    st.sidebar.subheader("📊 System Info")
    st.sidebar.info(f"**Version:** {config['app']['version']}")
    st.sidebar.info(f"**Model:** {config['claude']['model']}")
    
    # API usage warning
    st.sidebar.warning("⚠️ **Monitor API Usage**\nClaude API calls cost money. Check your Anthropic console regularly.")

def save_uploaded_file(uploaded_file) -> str:
    """Save uploaded file and return path"""
    os.makedirs("data/documents", exist_ok=True)
    file_path = f"data/documents/{uploaded_file.name}"
    
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    return file_path

def create_placeholder_files():
    """Create placeholder files for git"""
    placeholder_dirs = [
        "data/documents",
        "data/embeddings", 
        "data/processed"
    ]
    
    for dir_path in placeholder_dirs:
        os.makedirs(dir_path, exist_ok=True)
        gitkeep_path = f"{dir_path}/.gitkeep"
        if not os.path.exists(gitkeep_path):
            with open(gitkeep_path, 'w') as f:
                f.write("")