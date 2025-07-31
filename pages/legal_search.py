import streamlit as st
from typing import Optional
from backend.models import SearchResult
from utils.ui_components import display_document_snippet, display_search_summary, create_info_box, display_search_debug_info
from utils.session_state import clear_search_results

def show_legal_search_page():
    # Check if document is selected and show quick access
    from utils.session_state import has_selected_document
    if has_selected_document():
        st.info("📄 Document selected - use sidebar to view")
    
    backend = st.session_state.backend
    with st.container():
        # st.subheader("Search Configuration")
        
        # Query selection in a more compact layout
        col1, col2 = st.columns([3, 2])
        
        with col1:
            st.markdown("**Query Selection**")
            
            predefined_queries = backend.get_predefined_queries()
            query_options = ["Select predefined query..."] + [q.query_text for q in predefined_queries]
            
            selected_query_text = st.selectbox(
                "Predefined queries:",
                options=query_options,
                key="query_selector",
                label_visibility="collapsed"
            )
            
            selected_query = None
            if selected_query_text != "Select predefined query...":
                selected_query = next(
                    (q for q in predefined_queries if q.query_text == selected_query_text),
                    None
                )
            
            custom_query = st.text_area(
                "Or enter custom query:",
                value=st.session_state.get('custom_query', ''),
                height=80,
                placeholder="Type your custom legal document query here...",
                key="custom_query_input"
            )
        
        with col2:
            # st.markdown("**Filters & Settings**")
            
            clients = backend.get_clients()
            selected_client = st.selectbox(
                "Client:",
                options=clients,
                index=clients.index(st.session_state.get('selected_client', 'All')),
                key="client_selector"
            )
            
            document_types = backend.get_document_types()
            selected_doc_type = st.selectbox(
                "Document type:",
                options=document_types,
                index=document_types.index(st.session_state.get('selected_doc_type', 'All')),
                key="doc_type_selector"
            )
            
            # Advanced search parameters in expander
            with st.expander("⚙️ Advanced", expanded=False):
                col2a, col2b = st.columns(2)
                with col2a:
                    num_results = st.selectbox(
                        "Results:",
                        options=[3, 5, 10, 15],
                        index=1,  # Default to 5
                        key="num_results"
                    )
                
                with col2b:
                    min_relevance = st.selectbox(
                        "Min relevance:",
                        options=[0.0, 0.1, 0.2, 0.3, 0.5],
                        index=0,  # Default to 0.0
                        key="min_relevance"
                    )
            
            st.markdown("<br>", unsafe_allow_html=True)  # Add some spacing
            search_button = st.button(
                "🔍 Search",
                type="secondary",
                use_container_width=True,
                key="search_button"
            )
    
    # Handle query selection logic - both can coexist, but predefined takes priority when searching
    final_query = None
    
    # Predefined query takes priority if selected
    if selected_query and selected_query_text != "Select predefined query...":
        final_query = selected_query.query_text
        # Show a note if both are filled
        if custom_query.strip():
            st.info("📝 Using predefined query. Custom query will be ignored.")
    elif custom_query.strip():
        final_query = custom_query.strip()
    
    if search_button:
        if final_query:
            with st.spinner("Searching documents..."):
                st.session_state.custom_query = custom_query
                st.session_state.selected_client = selected_client
                st.session_state.selected_doc_type = selected_doc_type
                
                search_results = backend.search_documents(
                    query=final_query,
                    client_filter=selected_client if selected_client != "All" else None,
                    document_type_filter=selected_doc_type if selected_doc_type != "All" else None,
                    top_k=num_results,
                    min_relevance=min_relevance
                )
                st.session_state.search_results = search_results
                
                # Log the search operation
                try:
                    from utils.usage_logger import log_search, log_predefined_query_usage
                    log_search(
                        query=final_query,
                        client_filter=selected_client if selected_client != "All" else None,
                        doc_type_filter=selected_doc_type if selected_doc_type != "All" else None,
                        result_count=search_results.total_documents,
                        processing_time=search_results.processing_time
                    )
                    
                    # Log predefined query usage if applicable
                    if selected_query:
                        log_predefined_query_usage(selected_query.id, selected_query.title)
                except Exception:
                    # Don't break the app if logging fails
                    pass
                
                # Add to search history
                from utils.session_state import add_to_search_history
                add_to_search_history(
                    final_query,
                    selected_client,
                    selected_doc_type,
                    search_results.total_documents,
                    search_results.processing_time
                )
        else:
            st.error("Please enter a custom query or select a predefined query.")
    
    if 'search_results' in st.session_state and st.session_state.search_results:
        results = st.session_state.search_results
        
        st.markdown("---")
        
        # Highlight the final query that was used
        st.markdown("### 🔍 Query used")
        st.markdown(f"""
        <div style="
            background-color: #f0f9ff;
            border: 1px solid #0ea5e9;
            border-radius: 0.5rem;
            padding: 1rem;
            margin-bottom: 1rem;
        ">
            <div style="color: #374151; font-style: italic;">
                "{results.query}"
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("### Search results")
        
        display_search_summary(
            results.summary,
            results.total_documents,
            results.processing_time
        )
        
        # Add search debug information
        display_search_debug_info(
            results.query,
            results.client_filter or "All clients",
            st.session_state.get('selected_doc_type', 'All'),
            len(results.snippets)
        )
        
        st.markdown("---")
        
        if results.snippets:
            st.markdown("### Document snippets")
            st.markdown("*Click on any snippet to view the full document*")
            
            for idx, snippet in enumerate(results.snippets):
                display_document_snippet(snippet, idx)
        else:
            create_info_box(
                "No results found",
                "No document snippets were found for your query. Try adjusting your search terms or client filter.",
                "warning"
            )
