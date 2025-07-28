"""
Document Viewer Page
Full document viewing interface matching the right side of the provided image
"""

import streamlit as st
from typing import Optional
from backend.models import FullDocument
from utils.session_state import clear_selected_document

def show_document_viewer_page():
    """Display the document viewer page"""
    
    # Navigation button at the top
    if st.button("← Back to search", type="secondary"):
        st.session_state.current_page = "search"
        st.rerun()
    
    st.markdown("---")
    
    # Get backend instance
    backend = st.session_state.backend
    # Check if a document is selected
    if 'selected_document' not in st.session_state or not st.session_state.selected_document:
        st.error("No document selected. Please go back to search and select a document.")
    
    # Get the full document
    document_id = st.session_state.selected_document
    document = backend.get_full_document(document_id)
    
    if not document:
        st.error("Document not found.")
        return
    
    # Document header with close button
    col1, col2 = st.columns([6, 1])
    with col1:
        st.title("📄 Document viewer")
        st.subheader(document.title)
    
    with col2:
        if st.button("✖️", help="Close document", key="close_doc"):
            clear_selected_document()
            st.rerun()
    
    # Document metadata
    with st.container():
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Client", document.client)
        
        with col2:
            st.metric("Document Type", document.document_type)
        
        with col3:
            st.metric("Date Created", document.date_created.strftime("%Y-%m-%d"))
        
        with col4:
            st.metric("Version", document.metadata.get("version", "N/A"))
    

    st.markdown("### Full document content")
    
    # Content display with syntax highlighting for readability
    with st.container():
        st.markdown("""
        <div style="background-color: #f8f9fa; padding: 1rem; border-radius: 0.5rem; border-left: 4px solid #007bff;">
        """, unsafe_allow_html=True)
        
        # Display the document content
        st.markdown(document.content)
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Document metadata section
    with st.expander("📋 Document Metadata"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Classification:**")
            st.write(document.metadata.get("classification", "N/A"))
            
            st.markdown("**Last Updated:**")
            st.write(document.metadata.get("last_updated", "N/A"))
        
        with col2:
            st.markdown("**Sections:**")
            for section in document.sections:
                st.write(f"• {section['title']} (Page {section['page']})")
    
    # Navigation buttons
    st.markdown("---")
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        if st.button("← Back to Search Results", type="primary", use_container_width=True):
            clear_selected_document()
            st.rerun()
    
    with col2:
        if st.button("📥 Export", use_container_width=True):
            st.info("Export functionality would be implemented here")
    
    with col3:
        if st.button("🔗 Share", use_container_width=True):
            st.info("Share functionality would be implemented here")
    
    # Additional actions
    with st.expander("🔧 Document Actions"):
        st.markdown("""
        **Available Actions:**
        - Export document as PDF
        - Share document link
        - Download original file
        - Add to favorites
        - Create citation
        
        *These actions would be connected to your backend system.*
        """)
        
        if st.button("Print Document", key="print_doc"):
            st.info("Print functionality would open the browser's print dialog")
    
    # Footer with document info
    st.markdown("---")
    st.caption(f"Document ID: {document.id} | Viewing: {document.title}")
