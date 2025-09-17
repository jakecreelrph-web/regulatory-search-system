# pages/3_System_Status.py
import streamlit as st
import os
import json
import pandas as pd
from datetime import datetime
from src.utils import setup_page_config, authenticate_user, display_sidebar_info, load_config
from src.search_engine import SearchEngine

# Page configuration
setup_page_config()

# Load configuration
config = load_config()

# Authentication  
authenticate_user(config)

st.title("📊 System Status")
st.markdown("Monitor your regulatory document search system performance and usage.")

# Sidebar
display_sidebar_info(config)

# Get system statistics
search_engine = SearchEngine(config)
stats = search_engine.get_system_stats()

# Overview metrics
st.subheader("📈 System Overview")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        label="📄 Total Documents", 
        value=stats["total_documents"],
        help="Number of processed documents in your knowledge base"
    )

with col2:
    st.metric(
        label="🧩 Text Chunks", 
        value=stats["total_chunks"],
        help="Number of searchable text segments"
    )

with col3:
    st.metric(
        label="🏛️ Regulators", 
        value=len(stats["regulators"]),
        help="Number of different regulatory agencies"
    )

with col4:
    st.metric(
        label="📋 Document Types", 
        value=len(stats["document_types"]),
        help="Variety of document types in your system"
    )

# Last update info
if stats["last_update"]:
    st.info(f"🕒 **Last Document Added:** {stats['last_update'].strftime('%Y-%m-%d at %H:%M')}")
else:
    st.warning("No documents have been uploaded yet.")

# System health
st.markdown("---")
st.subheader("🏥 System Health")

health_col1, health_col2 = st.columns(2)

with health_col1:
    # Check API key
    api_status = "✅ Connected" if "CLAUDE_API_KEY" in st.secrets else "❌ Not Configured"
    st.write(f"**Claude API:** {api_status}")
    
    # Check directories
    dirs_to_check = ["data/documents", "data/processed", "data/embeddings"]
    missing_dirs = [d for d in dirs_to_check if not os.path.exists(d)]
    
    if missing_dirs:
        st.write(f"**Directory Structure:** ❌ Missing: {', '.join(missing_dirs)}")
    else:
        st.write("**Directory Structure:** ✅ All directories present")

with health_col2:
    # Check embedding model
    try:
        from src.embeddings_manager import EmbeddingsManager
        embeddings_manager = EmbeddingsManager(config)
        embeddings_manager._load_model()
        st.write("**Embedding Model:** ✅ Loaded successfully")
    except Exception as e:
        st.write(f"**Embedding Model:** ❌ Error: {str(e)[:50]}...")
    
    # Check configuration
    if os.path.exists("config.yaml"):
        st.write("**Configuration:** ✅ Loaded")
    else:
        st.write("**Configuration:** ❌ Missing config.yaml")

# Detailed statistics
if stats["total_documents"] > 0:
    st.markdown("---")
    st.subheader("📊 Detailed Analytics")
    
    # Regulator breakdown
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**📋 Documents by Regulator**")
        if stats["regulators"]:
            # Count documents per regulator
            regulator_counts = {}
            processed_dir = "data/processed"
            
            for file in os.listdir(processed_dir):
                if file.endswith('.json'):
                    try:
                        with open(f"{processed_dir}/{file}", 'r') as f:
                            doc = json.load(f)
                            regulator = doc['analysis']['regulator']
                            regulator_counts[regulator] = regulator_counts.get(regulator, 0) + 1
                    except:
                        continue
            
            regulator_df = pd.DataFrame(
                list(regulator_counts.items()), 
                columns=['Regulator', 'Document Count']
            )
            st.dataframe(regulator_df, use_container_width=True, hide_index=True)
    
    with col2:
        st.write("**📄 Documents by Type**")
        # Count documents per type
        type_counts = {}
        processed_dir = "data/processed"
        
        for file in os.listdir(processed_dir):
            if file.endswith('.json'):
                try:
                    with open(f"{processed_dir}/{file}", 'r') as f:
                        doc = json.load(f)
                        doc_type = doc['analysis']['document_type']
                        type_counts[doc_type] = type_counts.get(doc_type, 0) + 1
                except:
                    continue
        
        type_df = pd.DataFrame(
            list(type_counts.items()), 
            columns=['Document Type', 'Count']
        )
        st.dataframe(type_df, use_container_width=True, hide_index=True)
    
    # Recent uploads
    st.markdown("---")
    st.subheader("📅 Recent Document Activity")
    
    # Load recent documents
    recent_docs = []
    processed_dir = "data/processed"
    
    for file in os.listdir(processed_dir):
        if file.endswith('.json'):
            try:
                with open(f"{processed_dir}/{file}", 'r') as f:
                    doc = json.load(f)
                    recent_docs.append({
                        "Filename": doc['filename'],
                        "Regulator": doc['analysis']['regulator'],
                        "Type": doc['analysis']['document_type'],
                        "Upload Date": doc['upload_date'],
                        "Size": f"{doc['text_length']:,} chars"
                    })
            except:
                continue
    
    if recent_docs:
        # Sort by upload date (most recent first)
        recent_docs.sort(key=lambda x: x['Upload Date'], reverse=True)
        
        # Show last 10 documents
        recent_df = pd.DataFrame(recent_docs[:10])
        recent_df['Upload Date'] = pd.to_datetime(recent_df['Upload Date']).dt.strftime('%Y-%m-%d %H:%M')
        
        st.dataframe(recent_df, use_container_width=True, hide_index=True)
    else:
        st.info("No recent document activity.")

# Storage usage
st.markdown("---")
st.subheader("💾 Storage Usage")

storage_col1, storage_col2, storage_col3 = st.columns(3)

def get_directory_size(directory):
    """Calculate directory size in MB"""
    if not os.path.exists(directory):
        return 0
    
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(directory):
        for filename in filenames:
            file_path = os.path.join(dirpath, filename)
            try:
                total_size += os.path.getsize(file_path)
            except:
                continue
    
    return total_size / (1024 * 1024)  # Convert to MB

with storage_col1:
    docs_size = get_directory_size("data/documents")
    st.metric("📁 Documents", f"{docs_size:.1f} MB")

with storage_col2:
    processed_size = get_directory_size("data/processed") 
    st.metric("⚙️ Processed", f"{processed_size:.1f} MB")

with storage_col3:
    embeddings_size = get_directory_size("data/embeddings")
    st.metric("🧠 Embeddings", f"{embeddings_size:.1f} MB")

total_size = docs_size + processed_size + embeddings_size
st.info(f"**Total Storage Used:** {total_size:.1f} MB")

# System maintenance
st.markdown("---")
st.subheader("🔧 System Maintenance")

maintenance_col1, maintenance_col2 = st.columns(2)

with maintenance_col1:
    st.write("**🧹 Cleanup Actions**")
    
    if st.button("🗑️ Clear Cache"):
        # Clear Streamlit cache
        st.cache_data.clear()
        st.cache_resource.clear()
        st.success("Cache cleared successfully!")
    
    if st.button("📊 Refresh Statistics"):
        st.rerun()

with maintenance_col2:
    st.write("**⚙️ Configuration**")
    
    st.write(f"**Model:** {config['claude']['model']}")
    st.write(f"**Chunk Size:** {config['embeddings']['chunk_size']}")
    st.write(f"**Max Results:** {config['search']['max_results']}")
    st.write(f"**Similarity Threshold:** {config['search']['similarity_threshold']}")

# Warnings and recommendations  
st.markdown("---")
st.subheader("⚠️ Recommendations")

if stats["total_documents"] == 0:
    st.warning("📤 **No documents uploaded** - Upload some regulatory documents to get started")

elif stats["total_documents"] < 5:
    st.info("📈 **Limited content** - Upload more documents for better search results")

if len(stats["regulators"]) == 1:
    st.info("🏛️ **Single regulator** - Consider adding documents from other regulatory agencies")

if total_size > 500:
    st.warning(f"💾 **High storage usage** ({total_size:.1f} MB) - Consider removing old or duplicate documents")

st.success("🎯 **System is operational** - Ready for document search and upload")