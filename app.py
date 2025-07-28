"""
Legal Document Search UI
"""

import streamlit as st
from backend.fastapi_client import FastAPIRAGClient
from utils.session_state import initialize_session_state, has_selected_document
from utils.ui_components import setup_page_config


setup_page_config()


initialize_session_state()


if 'backend' not in st.session_state:
    st.session_state.backend = FastAPIRAGClient()

def main():
    """Main application entry point"""
    
    # Initialize current page if not set
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "search"
    
    # Load the appropriate page
    if st.session_state.current_page == "search":
        from pages.legal_search import show_legal_search_page
        show_legal_search_page()
    elif st.session_state.current_page == "document_viewer":
        from pages.document_viewer import show_document_viewer_page
        show_document_viewer_page()

if __name__ == "__main__":
    main()
