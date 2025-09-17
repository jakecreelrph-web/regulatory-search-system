# pages/2_Search_Documents.py
import streamlit as st
from datetime import datetime, date
import traceback

# Try to import our modules with error handling
try:
    from src.utils import setup_page_config, authenticate_user, display_sidebar_info, load_config
    st.success("✅ Utils imported successfully")
except Exception as e:
    st.error(f"❌ Failed to import utils: {e}")
    st.stop()

try:
    from src.search_engine import SearchEngine
    st.success("✅ SearchEngine imported successfully")
except Exception as e:
    st.error(f"❌ Failed to import SearchEngine: {e}")
    st.write("Full error:")
    st.code(str(e))
    st.stop()

# Page configuration
setup_page_config()

# Load configuration
try:
    config = load_config()
    st.success("✅ Config loaded successfully")
except Exception as e:
    st.error(f"❌ Failed to load config: {e}")
    st.stop()

# Authentication
authenticate_user(config)

st.title("🔍 Search Documents")
st.markdown("Use natural language to search your regulatory knowledge base.")

# Sidebar
display_sidebar_info(config)

# Initialize search engine with error handling
try:
    search_engine = SearchEngine(config)
    stats = search_engine.get_system_stats()
    st.success("✅ Search engine initialized successfully")
    st.write(f"System stats: {stats['total_documents']} documents, {stats['total_chunks']} chunks")
except Exception as e:
    st.error(f"❌ Failed to initialize search engine: {e}")
    st.write("Full error details:")
    st.code(traceback.format_exc())
    st.stop()

if stats["total_documents"] == 0:
    st.warning("📤 No documents uploaded yet! Go to Upload Documents to add files to your knowledge base.")
    st.stop()

# Search interface
st.subheader("🎯 Search Query")
query = st.text_input(
    "Enter your search query:",
    placeholder="e.g., 'What are the FDA requirements for software validation?'",
    help="Use natural language. Be specific about what you're looking for."
)

# Search filters
with st.expander("🔧 Advanced Filters"):
    col1, col2, col3 = st.columns(3)
    
    with col1:
        selected_regulator = st.selectbox(
            "Regulator",
            ["All"] + stats["regulators"]
        )
    
    with col2:
        selected_doc_type = st.selectbox(
            "Document Type", 
            ["All"] + stats["document_types"]
        )
    
    with col3:
        max_results = st.slider("Max Results", 5, 20, 10)

    # Date filters
    col4, col5 = st.columns(2)
    with col4:
        date_from = st.date_input("From Date", value=None)
    with col5:
        date_to = st.date_input("To Date", value=None)

# Search execution
if query:
    if st.button("🔍 Search", type="primary"):
        st.write("🎉 DEBUG: Search button clicked!")
        st.write(f"Query: '{query}'")
        
        try:
            # Prepare filters
            filters = {}
            if selected_regulator != "All":
                filters['regulator'] = selected_regulator
            if selected_doc_type != "All":
                filters['document_type'] = selected_doc_type
            if date_from:
                filters['date_from'] = date_from
            if date_to:
                filters['date_to'] = date_to
            
            st.write("✅ DEBUG: Filters prepared")
            st.write(f"Filters: {filters}")
            
            # Execute search
            st.write("🔍 DEBUG: Starting document search...")
            
            with st.spinner("🤖 Searching documents..."):
                results = search_engine.search_documents(query, filters)
            
            st.write(f"✅ DEBUG: Search completed! Found {len(results)} results")
            
            if results:
                # Generate AI summary
                st.write("🧠 DEBUG: Generating AI summary...")
                
                with st.spinner("🧠 Generating AI analysis..."):
                    ai_summary = search_engine.generate_ai_summary(query, results)
                
                st.write("✅ DEBUG: AI summary generated")
                
                # Display AI summary
                st.subheader("🤖 AI Analysis")
                st.markdown("**Based on your regulatory documents, here's what I found:**")
                st.markdown(ai_summary)
                
                # Display search results
                st.markdown("---")
                st.subheader(f"📄 Search Results ({len(results)} documents)")
                
                st.write("📋 DEBUG: Displaying results...")
                
                for i, result in enumerate(results):
                    doc = result['document']
                    similarity = result['best_similarity']
                    
                    with st.expander(f"📋 {doc['filename']} (Relevance: {similarity:.1%})"):
                        # Document metadata
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            st.write(f"**Regulator:** {doc['analysis']['regulator']}")
                            st.write(f"**Document Type:** {doc['analysis']['document_type']}")
                        
                        with col2:
                            st.write(f"**Upload Date:** {doc['upload_date'][:10]}")
                            st.write(f"**Matching Sections:** {result['total_matches']}")
                        
                        with col3:
                            st.write(f"**File Type:** {doc['file_type'].upper()}")
                            st.write(f"**Size:** {doc['text_length']:,} chars")
                        
                        # Document analysis
                        st.write(f"**Summary:** {doc['analysis']['summary']}")
                        
                        if doc['analysis']['key_requirements']:
                            st.write("**Key Requirements:**")
                            for req in doc['analysis']['key_requirements'][:3]:
                                st.write(f"• {req}")
                        
                        if doc['analysis']['subject_areas']:
                            st.write(f"**Subject Areas:** {', '.join(doc['analysis']['subject_areas'])}")
                        
                        # Show most relevant excerpts
                        st.markdown("**📝 Most Relevant Excerpts:**")
                        for j, chunk in enumerate(result['matching_chunks'][:2]):
                            st.markdown(f"*Excerpt {j+1} (Similarity: {chunk['similarity']:.1%}):*")
                            st.text(chunk['chunk_text'][:500] + "...")
                            if j < len(result['matching_chunks']) - 1:
                                st.markdown("---")
                
                st.success("🎉 DEBUG: All results displayed successfully!")
                
            else:
                st.warning("⚠️ No relevant documents found. Try:")
                st.markdown("""
                - **Broader terms** - Try more general keywords
                - **Different wording** - Rephrase your question  
                - **Check filters** - Remove restrictive filters
                - **Upload more documents** - Add more relevant files
                """)
        
        except Exception as e:
            st.error(f"🚨 SEARCH ERROR: {str(e)}")
            st.write("**Full error traceback:**")
            st.code(traceback.format_exc())
            
            # Additional debugging info
            st.write("**Debug Information:**")
            st.write(f"- Query: {query}")
            st.write(f"- Filters: {filters if 'filters' in locals() else 'Not created'}")
            st.write(f"- Search engine initialized: {'Yes' if 'search_engine' in locals() else 'No'}")

else:
    st.info("👆 Enter a search query above to get started")

# Sample queries
st.markdown("---")
st.subheader("💡 Sample Queries")

sample_queries = [
    "What are the FDA requirements for medical device software validation?",
    "OSHA bloodborne pathogen exposure control plan requirements",
    "EPA hazardous waste disposal regulations for laboratories", 
    "DEA controlled substance inventory requirements",
    "State pharmacy board technician training mandates"
]

st.markdown("**Try these example searches:**")
for query_example in sample_queries:
    if st.button(f"🔍 {query_example}", key=f"sample_{hash(query_example)}"):
        st.experimental_set_query_params(q=query_example)
        st.rerun()

# Search tips
st.markdown("---")
st.markdown("""
### 🎯 Search Tips

**For best results:**
- **Be specific** about what you need to know
- **Use regulatory language** when possible
- **Ask complete questions** rather than just keywords
- **Include the regulator** if you know it (FDA, OSHA, EPA, etc.)

**Example good queries:**
- "What documentation is required for FDA 510(k) submissions?"
- "How often must OSHA safety training be conducted?"
- "What are the DEA requirements for controlled substance storage?"

**The AI will:**
- Find relevant documents in your knowledge base
- Provide a comprehensive answer
- Highlight key requirements and compliance points
- Reference specific documents and sections
""")

# Debug information at bottom
st.markdown("---")
st.markdown("### 🐛 Debug Information")
st.write(f"**Total Documents:** {stats['total_documents']}")
st.write(f"**Total Chunks:** {stats['total_chunks']}")
st.write(f"**Available Regulators:** {stats['regulators']}")
st.write(f"**Available Document Types:** {stats['document_types']}")

if st.button("🔄 Test System"):
    st.write("**System Test Results:**")
    
    # Test imports
    try:
        from src.search_engine import SearchEngine
        st.success("✅ SearchEngine import works")
    except Exception as e:
        st.error(f"❌ SearchEngine import failed: {e}")
    
    # Test config
    try:
        config_test = load_config()
        st.success("✅ Config loading works")
    except Exception as e:
        st.error(f"❌ Config loading failed: {e}")
    
    # Test Claude API
    try:
        if "CLAUDE_API_KEY" in st.secrets:
            st.success("✅ Claude API key found in secrets")
        else:
            st.error("❌ Claude API key not found in secrets")
    except Exception as e:
        st.error(f"❌ Error checking Claude API key: {e}")
    
    # Test file structure
    import os
    required_dirs = ["data/processed", "data/embeddings"]
    for dir_path in required_dirs:
        if os.path.exists(dir_path):
            file_count = len([f for f in os.listdir(dir_path) if not f.startswith('.')])
            st.success(f"✅ {dir_path} exists with {file_count} files")
        else:
            st.error(f"❌ {dir_path} directory missing")