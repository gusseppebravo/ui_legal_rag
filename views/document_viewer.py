import streamlit as st
from utils.session_state import clear_selected_document

def show_document_viewer_page():
    if 'selected_document' not in st.session_state or not st.session_state.selected_document:
        st.error("No document selected. Please go back to search and select a document.")
        return
    
    # Check for single, multi-client, or all questions search results
    has_single_results = 'search_results' in st.session_state and st.session_state.search_results
    has_multi_results = 'multi_search_results' in st.session_state and st.session_state.multi_search_results
    has_all_questions = 'all_questions_results' in st.session_state and st.session_state.all_questions_results
    
    if not has_single_results and not has_multi_results and not has_all_questions:
        st.error("No search results found. Please go back and perform a search first.")
        return
    
    document_id = st.session_state.selected_document
    
    # Find the selected snippet from search results
    selected_snippet = None
    
    # First try single client search results
    if has_single_results:
        search_results = st.session_state.search_results
        for snippet in search_results.snippets:
            if snippet.id == document_id:
                selected_snippet = snippet
                break
    
    # If not found, try multi-client search results
    if not selected_snippet and has_multi_results:
        multi_results = st.session_state.multi_search_results
        if multi_results.client_search_results:
            for client, client_results in multi_results.client_search_results.items():
                for snippet in client_results.snippets:
                    if snippet.id == document_id:
                        selected_snippet = snippet
                        break
                if selected_snippet:
                    break
    
    # If not found, try all questions results
    if not selected_snippet and has_all_questions:
        all_q_results = st.session_state.all_questions_results
        if 'search_results' in all_q_results:
            for question, client_results in all_q_results['search_results'].items():
                for client, search_result in client_results.items():
                    if search_result and search_result.snippets:
                        for snippet in search_result.snippets:
                            if snippet.id == document_id:
                                selected_snippet = snippet
                                break
                        if selected_snippet:
                            break
                    if selected_snippet:
                        break
                if selected_snippet:
                    break
    
    if not selected_snippet:
        st.error("Selected document not found in search results.")
        return
    
    # Header - more compact
    col1, col2 = st.columns([5, 1])
    with col1:
        st.subheader("📄 Document Chunk")
        st.markdown(f"**{selected_snippet.title}**")
    
    with col2:
        if st.button("✖️", help="Close document", key="close_doc"):
            clear_selected_document()
            st.rerun()
    
    st.markdown("---")
    
    # Document content - immediately after title
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
    
    st.markdown("---")
    
    # Comprehensive metadata table
    st.markdown("### 📋 Document details")
    
    # Use shared utility for metadata table
    from utils.document_metadata import build_metadata_table, format_metadata_table
    
    metadata_rows = build_metadata_table(selected_snippet, include_basic_fields=True)
    table_content = format_metadata_table(metadata_rows)
    st.markdown(table_content)
    
    # Download file section
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
