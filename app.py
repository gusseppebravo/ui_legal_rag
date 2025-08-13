import streamlit as st
from backend.rag_client import RAGClient
from utils.session_state import initialize_session_state
from utils.ui_components import setup_page_config

setup_page_config()
initialize_session_state()

if 'backend' not in st.session_state:
    # st.session_state.backend = RAGClient(use_cache=False)
    st.session_state.backend = RAGClient(use_cache=True)

def show_sidebar():
    """Display sidebar with navigation and quick stats"""
    with st.sidebar:
        # st.logo("assets/contract.png", size='large')
        st.markdown("# :material/contract: CONTRACT INTELLIGENCE")
        st.markdown("---")
        
        # User info and logout button
        if st.session_state.get('authenticated', False):
            user_type = "Admin" if st.session_state.get('is_admin', False) else "User"
            st.markdown(f"**👤 Welcome, {st.session_state.get('username', 'User')} ({user_type})**")
            
            # Admin navigation
            if st.session_state.get('is_admin', False):
                if st.button("Analytics", use_container_width=True, 
                           type="primary" if st.session_state.current_page == "analytics" else "secondary"):
                    st.session_state.current_page = "analytics"
                    st.rerun()
                
                if st.button("Cache management", use_container_width=True,
                           type="primary" if st.session_state.current_page == "cache_management" else "secondary"):
                    st.session_state.current_page = "cache_management"
                    st.rerun()
                
                if st.button("Search", use_container_width=True,
                           type="primary" if st.session_state.current_page == "search" else "secondary"):
                    # Check if server is ready for search
                    if not st.session_state.get('server_ready', False):
                        st.session_state.current_page = "server_status"
                    else:
                        st.session_state.current_page = "search"
                    st.rerun()
            
            if st.button("Logout", use_container_width=True, type="secondary"):
                from views.login import logout
                logout()
            st.markdown("---")
        
        # Filters first (moved from legal_search.py)
        st.markdown("### 🔧 Filters")
        
        backend = st.session_state.backend
        
        # Account type filter
        account_types = backend.get_account_types()
        try:
            default_index = account_types.index('Client')
        except ValueError:
            default_index = 0
        
        selected_account_type = st.selectbox(
            "Account type:",
            options=account_types,
            index=default_index,
            key="account_type_selector"
        )
        
        document_types = backend.get_document_types()
        selected_doc_type = st.selectbox(
            "Document type:",
            options=document_types,
            index=document_types.index(st.session_state.get('selected_doc_type', 'All')),
            key="doc_type_selector"
        )
        
        # Conditional filters for Client account type
        if selected_account_type == "Client":
            accounts = backend.get_accounts_by_type("Client")
            
            selected_clients = st.multiselect(
                "Account(s):",
                options=accounts,
                default=st.session_state.get('client_selector', []),
                key="client_selector"
            )
            
            solution_lines = backend.get_solution_lines()
            selected_solution_line = st.selectbox(
                "Solution line:",
                options=solution_lines,
                index=solution_lines.index(st.session_state.get('selected_solution_line', 'All')),
                key="solution_line_selector"
            )
            
            related_products = backend.get_related_products()
            selected_related_product = st.selectbox(
                "Related product:",
                options=related_products,
                index=related_products.index(st.session_state.get('selected_related_product', 'All')),
                key="related_product_selector"
            )
        elif selected_account_type == "Vendor":
            accounts = backend.get_accounts_by_type("Vendor")
            
            selected_clients = st.multiselect(
                "Account(s):",
                options=accounts,
                default=st.session_state.get('client_selector', []),
                key="client_selector"
            )
        else:
            accounts = backend.get_accounts_by_type("All")
            
            selected_clients = st.multiselect(
                "Account(s):",
                options=accounts,
                default=st.session_state.get('client_selector', []),
                key="client_selector"
            )
        
        # Advanced search parameters
        with st.expander("⚙️ Advanced", expanded=False):
            num_results = st.selectbox(
                "Results:",
                options=[3, 5, 10, 15],
                index=1,
                key="num_results"
            )
            
            min_relevance = st.selectbox(
                "Min relevance:",
                options=[0.0, 0.1, 0.2, 0.3, 0.5],
                index=0,
                key="min_relevance"
            )
        
        # Clear filters button
        if st.button("🔄 Clear", use_container_width=True, type="secondary"):
            # Log filter clear action
            try:
                from utils.usage_logger import log_filter_usage
                log_filter_usage({
                    "action": "clear_all",
                    "account_type": st.session_state.get('account_type_selector'),
                    "doc_type": st.session_state.get('doc_type_selector'),
                    "clients": st.session_state.get('client_selector'),
                    "solution_line": st.session_state.get('solution_line_selector'),
                    "related_product": st.session_state.get('related_product_selector')
                })
            except Exception:
                pass
            
            # Clear all filter-related session state
            keys_to_clear = [
                'account_type_selector', 'doc_type_selector', 'client_selector',
                'solution_line_selector', 'related_product_selector', 'num_results',
                'min_relevance', 'query_selector', 'custom_query_input',
                'selected_clients', 'selected_doc_type', 'selected_account_type',
                'selected_solution_line', 'selected_related_product', 'custom_query',
                'search_results', 'multi_search_results', 'all_questions_results'
            ]
            for key in keys_to_clear:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()
        
        st.markdown("---")
        
        # Document viewer button (only show when a document is selected)
        from utils.session_state import has_selected_document
        if has_selected_document():
            if st.button("📄 View document", use_container_width=True, type="primary" if st.session_state.current_page == "document_viewer" else "secondary"):
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
        
        # App info popover (only for admin users)
        if st.session_state.get('is_admin', False):
            from utils.app_info import show_app_info_popover
            show_app_info_popover()
        
        if 'search_results' in st.session_state and st.session_state.search_results:
            st.markdown("**Last search**")
            results = st.session_state.search_results
            st.metric("Results", results.total_documents)
            st.metric("Time", f"{results.processing_time:.2f}s")
        
        # Search history
        from utils.session_state import get_search_history
        history = get_search_history()
        if history:
            st.markdown("**Recent searches**")
            for i, item in enumerate(history[:3]):  # Show last 3 searches
                doc_type_info = f" | Type: {item.get('document_type_filter', 'All')}" if item.get('document_type_filter') != 'All' else ""
                if st.button(
                    f"🕒 {item['query'][:30]}..." if len(item['query']) > 30 else f"🕒 {item['query']}", 
                    key=f"history_{i}",
                    help=f"Client: {item['client_filter']}{doc_type_info} | Results: {item['results_count']} | {item['timestamp']}"
                ):
                    # Log search history replay
                    try:
                        from utils.usage_logger import log_navigation
                        log_navigation("search_history", "search")
                    except Exception:
                        pass
                    
                    # Replay the search
                    st.session_state.custom_query_input = item['query']
                    # Handle both single and multi-client filters
                    if ',' in item['client_filter']:
                        # Multi-client search
                        clients = [c.strip() for c in item['client_filter'].split(',')]
                        st.session_state.client_selector = clients
                    else:
                        # Single client search  
                        st.session_state.client_selector = [item['client_filter']] if item['client_filter'] != "All" else []
                    st.session_state.doc_type_selector = item.get('document_type_filter', 'All')
                    st.session_state.current_page = "search"
                    st.rerun()

def show_top_nav():
    """Display top navigation bar"""
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        if st.session_state.current_page == "search":
            # Center the logo using columns
            left, col_center, right = st.columns([20, 1, 1])
            with left:
                st.image("assets/logo.png")
        elif st.session_state.current_page == "analytics":
            st.image("assets/logo.png")
        else:
            st.image("assets/file.png")
    
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
    # Initialize session state
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "login"
    if 'server_ready' not in st.session_state:
        st.session_state.server_ready = False
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'is_admin' not in st.session_state:
        st.session_state.is_admin = False
    
    # Log session start if this is a new session
    if 'session_logged' not in st.session_state:
        try:
            from utils.usage_logger import log_session_start
            log_session_start()
            st.session_state.session_logged = True
        except Exception:
            pass
    
    # Check authentication first
    from views.login import check_authentication
    
    if not check_authentication():
        # If not authenticated, show login page
        st.session_state.current_page = "login"
        from views.login import show_login_page
        show_login_page()
        return
    
    # Show server status page first if server is not ready (but not for analytics or cache management)
    if (not st.session_state.server_ready and 
        st.session_state.current_page not in ["login", "server_status", "analytics", "cache_management"]):
        st.session_state.current_page = "server_status"
    
    # Only show sidebar and nav for main app pages
    if st.session_state.current_page not in ["login", "server_status"]:
        show_sidebar()
        show_top_nav()
    elif st.session_state.current_page == "server_status":
        # Show minimal sidebar with just user info and logout
        with st.sidebar:
            st.markdown("# :material/contract: CONTRACT INTELLIGENCE")
            st.markdown("---")
            if st.session_state.get('authenticated', False):
                user_type = "Admin" if st.session_state.get('is_admin', False) else "User"
                st.markdown(f"**👤 Welcome, {st.session_state.get('username', 'User')} ({user_type})**")
                if st.button("🚪 Logout", use_container_width=True, type="secondary"):
                    from views.login import logout
                    logout()
    
    if st.session_state.current_page == "server_status":
        from views.server_status import show_server_status_page
        show_server_status_page()
    elif st.session_state.current_page == "search":
        from views.legal_search import show_legal_search_page
        show_legal_search_page()
    elif st.session_state.current_page == "document_viewer":
        from views.document_viewer import show_document_viewer_page
        show_document_viewer_page()
    elif st.session_state.current_page == "analytics":
        # Only allow analytics for admin users
        if st.session_state.get('is_admin', False):
            from views.analytics import show_analytics_page
            show_analytics_page()
        else:
            st.error("Access denied. Admin privileges required.")
            st.session_state.current_page = "search"
            st.rerun()
    elif st.session_state.current_page == "cache_management":
        # Only allow cache management for admin users
        if st.session_state.get('is_admin', False):
            from views.cache_management import show_cache_management_page
            show_cache_management_page()
        else:
            st.error("Access denied. Admin privileges required.")
            st.session_state.current_page = "search"
            st.rerun()

if __name__ == "__main__":
    main()
