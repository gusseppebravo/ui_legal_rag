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
            st.markdown("**Query selection**")
            
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
            clients_without_all = [c for c in clients if c != "All"]
            
            selected_clients = st.multiselect(
                "Client(s):",
                options=clients_without_all,
                default=st.session_state.get('selected_clients', []),
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
        if final_query and selected_clients:
            with st.spinner("Searching documents..."):
                st.session_state.custom_query = custom_query
                st.session_state.selected_clients = selected_clients
                st.session_state.selected_doc_type = selected_doc_type
                
                if len(selected_clients) > 1:
                    # Multi-client search
                    multi_results = backend.search_multiple_clients(
                        query=final_query,
                        client_filters=selected_clients,
                        document_type_filter=selected_doc_type if selected_doc_type != "All" else None,
                        top_k=num_results
                    )
                    st.session_state.multi_search_results = multi_results
                    st.session_state.search_results = None
                else:
                    # Single client search
                    single_client = selected_clients[0] if selected_clients else None
                    search_results = backend.search_documents(
                        query=final_query,
                        client_filter=single_client,
                        document_type_filter=selected_doc_type if selected_doc_type != "All" else None,
                        top_k=num_results,
                        min_relevance=min_relevance
                    )
                    st.session_state.search_results = search_results
                    st.session_state.multi_search_results = None
                
                # Log the search operation
                try:
                    from utils.usage_logger import log_search, log_predefined_query_usage
                    if len(selected_clients) > 1:
                        log_search(
                            query=final_query,
                            client_filter=", ".join(selected_clients),
                            doc_type_filter=selected_doc_type if selected_doc_type != "All" else None,
                            result_count=len(selected_clients),
                            processing_time=multi_results.total_processing_time
                        )
                    else:
                        log_search(
                            query=final_query,
                            client_filter=selected_clients[0] if selected_clients else None,
                            doc_type_filter=selected_doc_type if selected_doc_type != "All" else None,
                            result_count=search_results.total_documents,
                            processing_time=search_results.processing_time
                        )
                    
                    if selected_query:
                        log_predefined_query_usage(selected_query.id, selected_query.title)
                except Exception:
                    pass
                
                # Add to search history
                from utils.session_state import add_to_search_history
                if len(selected_clients) > 1:
                    add_to_search_history(
                        final_query,
                        ", ".join(selected_clients),
                        selected_doc_type,
                        len(selected_clients),
                        multi_results.total_processing_time
                    )
                else:
                    add_to_search_history(
                        final_query,
                        selected_clients[0] if selected_clients else "None",
                        selected_doc_type,
                        search_results.total_documents,
                        search_results.processing_time
                    )
        else:
            if not final_query:
                st.error("Please enter a custom query or select a predefined query.")
            if not selected_clients:
                st.error("Please select at least one client.")
    
    # Display results - handle both single and multi-client
    if 'search_results' in st.session_state and st.session_state.search_results:
        # Single client results
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
            results.client_filter or "Selected client",
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
    
    elif 'multi_search_results' in st.session_state and st.session_state.multi_search_results:
        # Multi-client results
        multi_results = st.session_state.multi_search_results
        
        st.markdown("---")
        
        # Display tabular summary as the main answer (most important part first)
        st.markdown("### Answer")
        st.markdown(multi_results.tabular_summary)
        
        st.markdown("---")
        
        # Query used and search results section
        st.markdown("### Query used and search results")
        
        # Show the query used
        st.markdown("**Query:**")
        st.markdown(f"""
        <div style="
            background-color: #f0f9ff;
            border: 1px solid #0ea5e9;
            border-radius: 0.5rem;
            padding: 1rem;
            margin-bottom: 1rem;
        ">
            <div style="color: #374151; font-style: italic;">
                "{multi_results.query}"
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("**Search results:**")
        
        # Display processing time metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Clients searched", len(multi_results.client_results))
        with col2:
            st.metric("Total processing time", f"{multi_results.total_processing_time:.2f}s")
        with col3:
            st.metric("Search status", "✅ Complete")
        
        # Display individual client results in an expandable section
        if multi_results.client_search_results:
            with st.expander("📄 Individual client results (Click to expand)", expanded=False):
                client_tabs = st.tabs(list(multi_results.client_search_results.keys()))
                
                for i, (client, client_result) in enumerate(multi_results.client_search_results.items()):
                    with client_tabs[i]:
                        st.markdown(f"#### {client}")
                        
                        # Show client-specific summary
                        st.markdown("**AI answer:**")
                        st.markdown(f"""
                        <div style="
                            background-color: #f8f9fa;
                            border: 1px solid #dee2e6;
                            border-radius: 0.4rem;
                            padding: 0.8rem;
                            margin-bottom: 1rem;
                            font-size: 0.95rem;
                        ">
                            {client_result.summary}
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Show snippets for this client
                        if client_result.snippets:
                            st.markdown(f"**Document snippets ({len(client_result.snippets)}):**")
                            for idx, snippet in enumerate(client_result.snippets):
                                display_document_snippet(snippet, f"{client}_{idx}")
                        else:
                            st.info("No document snippets found for this client.")
