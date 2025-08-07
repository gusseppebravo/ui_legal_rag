import streamlit as st
import streamlit as st
from datetime import datetime

def initialize_session_state():
    if 'search_results' not in st.session_state:
        st.session_state.search_results = None
    
    if 'selected_query' not in st.session_state:
        st.session_state.selected_query = None
    
    if 'custom_query' not in st.session_state:
        st.session_state.custom_query = ""
    
    if 'selected_client' not in st.session_state:
        st.session_state.selected_client = "All"
    
    if 'selected_account_type' not in st.session_state:
        st.session_state.selected_account_type = "All"
    
    if 'selected_solution_line' not in st.session_state:
        st.session_state.selected_solution_line = "All"
    
    if 'selected_related_product' not in st.session_state:
        st.session_state.selected_related_product = "All"
    
    if 'selected_document' not in st.session_state:
        st.session_state.selected_document = None
    
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "search"
    
    if 'search_history' not in st.session_state:
        st.session_state.search_history = []
    
    # Log session start (only once per session)
    if 'session_logged' not in st.session_state:
        st.session_state.session_logged = True
        try:
            from .usage_logger import log_session_start
            log_session_start()
        except Exception:
            # Don't break the app if logging fails
            pass
    
    if 'search_history' not in st.session_state:
        st.session_state.search_history = []

def add_to_search_history(query: str, client_filter: str, document_type_filter: str, 
                         account_type_filter: str = None, solution_line_filter: str = None, 
                         related_product_filter: str = None, results_count: int = 0, processing_time: float = 0.0):
    """Add a search to the history"""
    history_item = {
        'query': query,
        'client_filter': client_filter or "All",
        'document_type_filter': document_type_filter or "All",
        'account_type_filter': account_type_filter or "All",
        'solution_line_filter': solution_line_filter or "All",
        'related_product_filter': related_product_filter or "All",
        'results_count': results_count,
        'processing_time': processing_time,
        'timestamp': datetime.now().strftime("%H:%M:%S")
    }
    
    # Keep only last 10 searches
    if len(st.session_state.search_history) >= 10:
        st.session_state.search_history.pop(0)
    
    st.session_state.search_history.append(history_item)

def get_search_history():
    """Get the search history"""
    return st.session_state.search_history[::-1]  # Most recent first

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
