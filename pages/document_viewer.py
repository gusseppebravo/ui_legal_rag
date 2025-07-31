import streamlit as st
from utils.session_state import clear_selected_document

def show_document_viewer_page():
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
    
    # Header - more compact
    col1, col2 = st.columns([5, 1])
    with col1:
        st.subheader("📄 Document Chunk")
        st.markdown(f"**{selected_snippet.title}**")
        
        # Extract contract number from s3_path
        contract_number = "N/A"
        if selected_snippet.metadata and 's3_path' in selected_snippet.metadata:
            s3_path = selected_snippet.metadata['s3_path']
            if '/contract-docs/' in s3_path:
                # Extract number after /contract-docs/
                path_parts = s3_path.split('/contract-docs/')
                if len(path_parts) > 1:
                    remaining_path = path_parts[1]
                    # Get the first directory after contract-docs/
                    contract_parts = remaining_path.split('/')
                    if contract_parts:
                        contract_number = contract_parts[0]
        
        # Display client and contract info
        client_name = selected_snippet.metadata.get("client_account", "N/A") if selected_snippet.metadata else "N/A"
        st.markdown(f"**Client:** {client_name} | **Contract:** {contract_number}")
    
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
        distance = f"{selected_snippet.distance:.3f}"
        st.metric("Distance", distance)
    
    st.markdown("---")
    
    # Document content - more compact
    st.markdown("### Content")
    
    st.markdown(f"""
    <div style="
        background-color: #f8f9fa; 
        padding: 1rem; 
        border-radius: 0.4rem; 
        border-left: 3px solid #007bff;
        margin: 0.5rem 0;
        line-height: 1.5;
        font-size: 0.95rem;
    ">
        {selected_snippet.content}
    </div>
    """, unsafe_allow_html=True)
    
    # Download file section - more compact
    if selected_snippet.metadata and 'presigned_url' in selected_snippet.metadata:
        presigned_url = selected_snippet.metadata['presigned_url']
        if presigned_url:
            st.markdown("### File Download")
            st.markdown(f"""
            <a href="{presigned_url}" target="_blank" style="text-decoration: none;">
                <button style="
                    padding: 0.5rem 1rem;
                    background-color: #10b981;
                    color: white;
                    border: none;
                    border-radius: 0.4rem;
                    font-weight: 500;
                    cursor: pointer;
                    font-size: 0.9rem;
                    transition: all 0.2s;
                " onmouseover="this.style.backgroundColor='#059669'" onmouseout="this.style.backgroundColor='#10b981'">
                    📥 Download file
                </button>
            </a>
            """, unsafe_allow_html=True)
    
    # Footer - compact
    st.markdown("---")
    st.caption(f"Chunk: {selected_snippet.id} | {selected_snippet.title}")
