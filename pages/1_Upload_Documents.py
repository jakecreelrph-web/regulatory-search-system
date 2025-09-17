# pages/1_Upload_Documents.py
import streamlit as st
import os
from src.utils import setup_page_config, authenticate_user, display_sidebar_info, load_config, save_uploaded_file
from src.document_processor import DocumentProcessor
from src.embeddings_manager import EmbeddingsManager

# Page configuration
setup_page_config()

# Load configuration
config = load_config()

# Authentication
authenticate_user(config)

st.title("📤 Upload Documents")
st.markdown("Upload regulatory documents to add them to your searchable knowledge base.")

# Sidebar
display_sidebar_info(config)

# File upload interface
st.subheader("📋 Upload New Documents")

uploaded_files = st.file_uploader(
    "Choose regulatory documents",
    type=['pdf', 'docx', 'txt'],
    accept_multiple_files=True,
    help="Supported formats: PDF, Word (.docx), Text (.txt)"
)

if uploaded_files:
    st.success(f"Selected {len(uploaded_files)} files for upload")
    
    # Display selected files
    for file in uploaded_files:
        st.write(f"📄 **{file.name}** ({file.size:,} bytes)")
    
    if st.button("🚀 Process Documents", type="primary"):
        # Initialize processors
        doc_processor = DocumentProcessor(config)
        embeddings_manager = EmbeddingsManager(config)
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        results_container = st.container()
        
        successful_uploads = 0
        failed_uploads = 0
        
        for i, uploaded_file in enumerate(uploaded_files):
            try:
                # Update progress
                progress = (i + 1) / len(uploaded_files)
                progress_bar.progress(progress)
                status_text.text(f"Processing {uploaded_file.name}...")
                
                # Save file
                file_path = save_uploaded_file(uploaded_file)
                
                # Process document
                document_data = doc_processor.process_document(file_path, uploaded_file.name)
                
                if document_data:
                    # Generate embeddings
                    embeddings_data = embeddings_manager.process_document_embeddings(document_data)
                    
                    # Display result
                    with results_container.expander(f"✅ {uploaded_file.name} - Processed Successfully"):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.write(f"**Document Type:** {document_data['analysis']['document_type']}")
                            st.write(f"**Regulator:** {document_data['analysis']['regulator']}")
                            st.write(f"**Text Length:** {document_data['text_length']:,} characters")
                        
                        with col2:
                            st.write(f"**Subject Areas:** {', '.join(document_data['analysis']['subject_areas'])}")
                            st.write(f"**Text Chunks:** {embeddings_data['num_chunks']}")
                            st.write(f"**Keywords:** {', '.join(document_data['analysis']['keywords'][:5])}")
                        
                        st.write(f"**Summary:** {document_data['analysis']['summary']}")
                    
                    successful_uploads += 1
                else:
                    failed_uploads += 1
                    with results_container.expander(f"❌ {uploaded_file.name} - Processing Failed"):
                        st.error("Failed to extract text or analyze document")
                
            except Exception as e:
                failed_uploads += 1
                with results_container.expander(f"❌ {uploaded_file.name} - Error"):
                    st.error(f"Error processing file: {str(e)}")
        
        # Final status
        progress_bar.progress(1.0)
        status_text.text("Processing complete!")
        
        # Summary
        if successful_uploads > 0:
            st.success(f"✅ Successfully processed {successful_uploads} documents")
        
        if failed_uploads > 0:
            st.error(f"❌ Failed to process {failed_uploads} documents")
        
        st.info("💡 Documents are now available for search. Go to the Search Documents page to find information.")

# Display existing documents
st.markdown("---")
st.subheader("📚 Uploaded Documents")

processed_dir = "data/processed"
if os.path.exists(processed_dir):
    processed_files = [f for f in os.listdir(processed_dir) if f.endswith('.json')]
    
    if processed_files:
        st.info(f"You have {len(processed_files)} documents in your knowledge base")
        
        # Load and display document list
        import json
        documents = []
        
        for file in processed_files:
            try:
                with open(f"{processed_dir}/{file}", 'r', encoding='utf-8') as f:
                    doc_data = json.load(f)
                    documents.append({
                        "Filename": doc_data['filename'],
                        "Regulator": doc_data['analysis']['regulator'],
                        "Type": doc_data['analysis']['document_type'],
                        "Upload Date": doc_data['upload_date'][:10],
                        "Size (chars)": f"{doc_data['text_length']:,}"
                    })
            except:
                continue
        
        if documents:
            import pandas as pd
            df = pd.DataFrame(documents)
            st.dataframe(df, use_container_width=True)
    else:
        st.warning("No documents uploaded yet. Upload some documents to get started!")
else:
    st.warning("No documents uploaded yet. Upload some documents to get started!")

# Usage tips
st.markdown("---")
st.markdown("""
### 💡 Upload Tips

- **Supported formats:** PDF, Word (.docx), Text (.txt)
- **File size limit:** 200MB per file
- **Best results:** Use official regulatory documents with clear text
- **Processing time:** ~30-60 seconds per document
- **AI Analysis:** Each document is analyzed by Claude AI for better search

### 📋 What Happens During Processing

1. **Text Extraction** - Extract readable text from your documents
2. **AI Analysis** - Claude identifies key information and requirements  
3. **Embedding Generation** - Create semantic vectors for search
4. **Metadata Storage** - Save document information for retrieval
""")