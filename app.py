import streamlit as st
from backend.rag_client import RAGClient
from utils.session_state import initialize_session_state
from utils.ui_components import setup_page_config

setup_page_config()
initialize_session_state()

if 'backend' not in st.session_state:
    st.session_state.backend = RAGClient()

def show_sidebar():
    """Display sidebar with navigation and quick stats"""
    with st.sidebar:
        st.markdown("### 📋 Legal RAG")
        st.markdown("---")
        
        # Navigation
        st.markdown("**Navigation**")
        if st.button("🔍 Search", use_container_width=True, type="primary" if st.session_state.current_page == "search" else "secondary"):
            # Log navigation
            try:
                from utils.usage_logger import log_navigation
                log_navigation(st.session_state.current_page, "search")
            except Exception:
                pass
            st.session_state.current_page = "search"
            st.rerun()
        
        from utils.session_state import has_selected_document
        if has_selected_document():
            if st.button("📄 Document", use_container_width=True, type="primary" if st.session_state.current_page == "document_viewer" else "secondary"):
                # Log navigation
                try:
                    from utils.usage_logger import log_navigation
                    log_navigation(st.session_state.current_page, "document_viewer")
                except Exception:
                    pass
                st.session_state.current_page = "document_viewer"
                st.rerun()
        
        st.markdown("---")
        
        # Quick stats
        backend = st.session_state.backend
        clients = backend.get_clients()
        queries = backend.get_predefined_queries()
        
        st.markdown("**Dataset Info**")
        st.metric("Clients", len(clients) - 1)  # -1 for "All"
        st.metric("Predefined Queries", len(queries))
        
        if 'search_results' in st.session_state and st.session_state.search_results:
            st.markdown("**Last Search**")
            results = st.session_state.search_results
            st.metric("Results", results.total_documents)
            st.metric("Time", f"{results.processing_time:.2f}s")
        
        # Search history
        from utils.session_state import get_search_history
        history = get_search_history()
        if history:
            st.markdown("**Recent Searches**")
            for i, item in enumerate(history[:3]):  # Show last 3 searches
                doc_type_info = f" | Type: {item.get('document_type_filter', 'All')}" if item.get('document_type_filter') != 'All' else ""
                if st.button(
                    f"🕒 {item['query'][:30]}..." if len(item['query']) > 30 else f"🕒 {item['query']}", 
                    key=f"history_{i}",
                    help=f"Client: {item['client_filter']}{doc_type_info} | Results: {item['results_count']} | {item['timestamp']}"
                ):
                    # Replay the search
                    st.session_state.custom_query_input = item['query']
                    st.session_state.client_selector = item['client_filter']
                    st.session_state.doc_type_selector = item.get('document_type_filter', 'All')
                    st.session_state.current_page = "search"
                    st.rerun()

def show_top_nav():
    """Display top navigation bar"""
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        if st.session_state.current_page == "search":
            st.markdown("# 🔍")
        else:
            st.markdown("# 📄")
    
    with col2:
        if st.session_state.current_page == "document_viewer":
            if st.button("← Back to Search", type="secondary"):
                st.session_state.current_page = "search"
                st.rerun()
    
    with col3:
        # Quick actions could go here
        pass
    
    st.markdown("---")

def main():
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "search"
    
    show_sidebar()
    show_top_nav()
    
    if st.session_state.current_page == "search":
        from pages.legal_search import show_legal_search_page
        show_legal_search_page()
    elif st.session_state.current_page == "document_viewer":
        from pages.document_viewer import show_document_viewer_page
        show_document_viewer_page()

if __name__ == "__main__":
    main()
