import streamlit as st

def initialize_session_state():
    if 'search_results' not in st.session_state:
        st.session_state.search_results = None
    
    if 'selected_query' not in st.session_state:
        st.session_state.selected_query = None
    
    if 'custom_query' not in st.session_state:
        st.session_state.custom_query = ""
    
    if 'selected_client' not in st.session_state:
        st.session_state.selected_client = "All"
    
    if 'selected_document' not in st.session_state:
        st.session_state.selected_document = None
    
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "search"

def clear_search_results():
    if 'search_results' in st.session_state:
        del st.session_state.search_results

def set_selected_document(document_id: str):
    st.session_state.selected_document = document_id
    st.session_state.current_page = "document_viewer"

def clear_selected_document():
    if 'selected_document' in st.session_state:
        del st.session_state.selected_document
    st.session_state.current_page = "search"

def has_selected_document() -> bool:
    return ('selected_document' in st.session_state and 
            st.session_state.selected_document is not None and 
            st.session_state.selected_document != "")
