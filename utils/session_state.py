"""
Session state management utilities
"""

import streamlit as st

def initialize_session_state():
    """Initialize session state variables"""
    
    # Search state
    if 'search_results' not in st.session_state:
        st.session_state.search_results = None
    
    if 'selected_query' not in st.session_state:
        st.session_state.selected_query = None
    
    if 'custom_query' not in st.session_state:
        st.session_state.custom_query = ""
    
    if 'selected_client' not in st.session_state:
        st.session_state.selected_client = "All"
    
    # Document viewer state
    if 'selected_document' not in st.session_state:
        st.session_state.selected_document = None
    
    # Navigation state
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "search"

def clear_search_results():
    """Clear search results from session state"""
    if 'search_results' in st.session_state:
        del st.session_state.search_results

def set_selected_document(document_id: str):
    """Set the selected document for viewing"""
    st.session_state.selected_document = document_id
    st.session_state.current_page = "document_viewer"

def clear_selected_document():
    """Clear the selected document"""
    if 'selected_document' in st.session_state:
        del st.session_state.selected_document
    st.session_state.current_page = "search"

def has_selected_document() -> bool:
    """Check if a document is currently selected"""
    return ('selected_document' in st.session_state and 
            st.session_state.selected_document is not None and 
            st.session_state.selected_document != "")
