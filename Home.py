import time
import streamlit as st

start_time = time.time()
st.write(" **Startup Timeing Debug:**")

# Time basic imports
basic_import_start = time.time()
import yaml
st.write(f" Basic imports: {time.time() - basic_import_start:.2f}s")

# Time utiliz import
utils_start = time.Time()
from src.utils import setup_page_config, authenticate_user, display_sidebar_info, load_config
st.write(f" Utils import: {time.time() - utils_start:.2f}s")

# Time Page setup
setup_start = time.time()
setup_page_config()
st.write(f" Page setup: {time.time() - setup_start:.2f}s")

#time config
config_start = time.time()
config = load_config()
st.write(f" Config Loading: {time.time() - config_start:.2f}s")

# Time authentication
auth_start = time.time()
authenticate_user(config)
st.write(f" Authentication: {time.time() - auth_start:.2f}s")

#Time Search engine import
engine_start = time.time()
from src.search_engine import SearchEngine
st.write(f" Search engine import: {time.time() - engine_start:.2f}s")

st.write(f" Total startup time: {time.time()  start_time:.2f} seconds**")
st.markdown("---")

# Home.py
import streamlit as st
import yaml
from src.utils import setup_page_config, authenticate_user, display_sidebar_info, load_config
from src.search_engine import SearchEngine
import os


os.environ['TOKENIZERS_PARALLELISM'] = 'false'

@st.cache_resource
def initialize_system():
    """Initialized system components once"""
    try:
        config = load_config()
        return config
    except Exception as e:
        st.error(f"System initialization failed: {e}")
        return None
config = initialize_system()
if config is None:
    st.stop()

# Page configuration
setup_page_config()

# Load configuration
config = load_config()

# Authentication
authenticate_user(config)

# Main interface
st.title("📋 Regulatory Document Search System")
st.markdown(f"**{config['app']['description']}**")

# Display system stats on home page
if st.button("🔄 Refresh System Stats"):
    search_engine = SearchEngine(config)
    stats = search_engine.get_system_stats()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📄 Total Documents", stats["total_documents"])
    
    with col2:
        st.metric("🧩 Text Chunks", stats["total_chunks"])
    
    with col3:
        st.metric("🏛️ Regulators", len(stats["regulators"]))
    
    with col4:
        st.metric("📋 Document Types", len(stats["document_types"]))
    
    if stats["last_update"]:
        st.info(f"**Last Update:** {stats['last_update'].strftime('%Y-%m-%d %H:%M')}")
    
    if stats["regulators"]:
        st.subheader("Available Regulators")
        st.write(", ".join(stats["regulators"]))
    
    if stats["document_types"]:
        st.subheader("Document Types")
        st.write(", ".join(stats["document_types"]))

# Navigation instructions
st.markdown("---")
st.markdown("""
### 🚀 Getting Started

1. **📤 Upload Documents** - Use the Upload Documents page to add regulatory files
2. **🔍 Search Documents** - Use natural language to search your knowledge base  
3. **📊 System Status** - Monitor system performance and usage

### 💡 Search Tips

- Use natural language: *"What are the requirements for pharmacy technician training in Ohio?"*
- Be specific: *"FDA guidance on software validation"*
- Ask about compliance: *"What do I need to know about OSHA bloodborne pathogen standards?"*
""")

# Sidebar
display_sidebar_info(config)

# Quick search from home page
st.markdown("---")
st.subheader("🔍 Quick Search")
quick_query = st.text_input("Enter your search query:", placeholder="e.g., 'FDA device registration requirements'")

if quick_query:
    if st.button("Search Now"):
        search_engine = SearchEngine(config)
        results = search_engine.search_documents(quick_query)
        
        if results:
            st.success(f"Found {len(results)} relevant documents")
            for i, result in enumerate(results[:3]):
                doc = result['document']
                with st.expander(f"📄 {doc['filename']} (Similarity: {result['best_similarity']:.1%})"):
                    st.write(f"**Regulator:** {doc['analysis']['regulator']}")
                    st.write(f"**Type:** {doc['analysis']['document_type']}")
                    st.write(f"**Summary:** {doc['analysis']['summary']}")
            
            st.info("Go to Search Documents page for full results and AI analysis")
        else:
            st.warning("No documents found. Try uploading some documents first!")
