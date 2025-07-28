import streamlit as st
from utils.session_state import clear_selected_document

def show_document_viewer_page():
    if st.button("← Back to search", type="secondary"):
        st.session_state.current_page = "search"
        st.rerun()
    
    st.markdown("---")
    
    if 'selected_document' not in st.session_state or not st.session_state.selected_document:
        st.error("No document selected. Please go back to search and select a document.")
        return
    
    if 'search_results' not in st.session_state or not st.session_state.search_results:
        st.error("No search results found. Please go back and perform a search first.")
        return
    
    document_id = st.session_state.selected_document
    search_results = st.session_state.search_results
    
    # Find the selected snippet from search results
    selected_snippet = None
    for snippet in search_results.snippets:
        if snippet.id == document_id:
            selected_snippet = snippet
            break
    
    if not selected_snippet:
        st.error("Selected document not found in search results.")
        return
    
    # Header
    col1, col2 = st.columns([6, 1])
    with col1:
        st.title("📄 Document chunk viewer")
        st.subheader(selected_snippet.title)
    
    with col2:
        if st.button("✖️", help="Close document", key="close_doc"):
            clear_selected_document()
            st.rerun()
    
    # Document metadata
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Source", selected_snippet.source)
    
    with col2:
        st.metric("Document type", selected_snippet.section or 'N/A')
    
    with col3:
        relevance = f"{selected_snippet.relevance_score:.3f}"
        st.metric("Relevance", relevance)
    
    with col4:
        distance = selected_snippet.metadata.get('distance', 'N/A') if selected_snippet.metadata else 'N/A'
        st.metric("Distance", distance)
    
    st.markdown("---")
    
    # Document content
    st.markdown("### Chunk content")
    
    st.markdown(f"""
    <div style="
        background-color: #f8f9fa; 
        padding: 1.5rem; 
        border-radius: 0.5rem; 
        border-left: 4px solid #007bff;
        margin: 1rem 0;
        line-height: 1.6;
        font-size: 1.1rem;
    ">
        {selected_snippet.content}
    </div>
    """, unsafe_allow_html=True)
    
    # Download file section
    if selected_snippet.metadata and 'presigned_url' in selected_snippet.metadata:
        presigned_url = selected_snippet.metadata['presigned_url']
        if presigned_url:
            st.markdown("### File access")
            st.markdown("Download the complete document file:")
            st.markdown(f"""
            <a href="{presigned_url}" target="_blank" style="text-decoration: none;">
                <button style="
                    padding: 0.75rem 1.5rem;
                    background-color: #10b981;
                    color: white;
                    border: none;
                    border-radius: 0.5rem;
                    font-weight: 500;
                    cursor: pointer;
                    font-size: 1rem;
                    transition: all 0.2s;
                " onmouseover="this.style.backgroundColor='#059669'" onmouseout="this.style.backgroundColor='#10b981'">
                    📥 Download file
                </button>
            </a>
            """, unsafe_allow_html=True)
    
    # Additional metadata
    if selected_snippet.metadata:
        with st.expander("📋 Additional metadata"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**File path:**")
                s3_path = selected_snippet.metadata.get("s3_path", "N/A")
                st.code(s3_path, language=None)
                
                st.markdown("**Client account:**")
                st.write(selected_snippet.metadata.get("client_account", "N/A"))
            
            with col2:
                st.markdown("**File name:**")
                st.write(selected_snippet.metadata.get("file_name", "N/A"))
                
                st.markdown("**Chunk metadata:**")
                for key, value in selected_snippet.metadata.items():
                    if key not in ['presigned_url', 's3_path', 'client_account', 'file_name', 'text']:
                        st.write(f"• **{key}:** {value}")
    
    # Navigation
    st.markdown("---")
    col1, col2 = st.columns([3, 1])
    
    with col1:
        if st.button("← Back to search results", type="primary", use_container_width=True):
            clear_selected_document()
            st.rerun()
    
    with col2:
        # Show current query info
        if search_results.query:
            st.info(f"Query: {search_results.query[:50]}...")
    
    # Footer
    st.markdown("---")
    st.caption(f"Chunk ID: {selected_snippet.id} | Document: {selected_snippet.title}")
