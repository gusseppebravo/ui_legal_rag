"""
Legal Document Search Page
Main search interface matching the left side of the provided image
"""

import streamlit as st
from typing import Optional
from backend.models import SearchResult
from utils.ui_components import display_document_snippet, display_search_summary, create_info_box
from utils.session_state import clear_search_results

def show_legal_search_page():
    """Display the main legal document search page"""
    # Page header with navigation
    st.markdown("""
    <div class="search-header">
        <h1>📋 Legal document search</h1>
        <p style="margin: 0.5rem 0 0 0; opacity: 0.9;">Search and analyze legal documents with AI-powered retrieval</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Show document viewer button if a document is selected
    from utils.session_state import has_selected_document
    if has_selected_document():
        if st.button("📄 View selected document", type="secondary", use_container_width=True):
            st.session_state.current_page = "document_viewer"
            st.rerun()
        st.markdown("---")
    
    # Get backend instance
    backend = st.session_state.backend
    
    # Main search form
    with st.container():
        st.markdown("### Search configuration")
        
        # Query selection section
        st.markdown("**Select query**")
        
        # Get predefined queries
        predefined_queries = backend.get_predefined_queries()
        query_options = ["Select a predefined query..."] + [q.title for q in predefined_queries]
        
        selected_query_title = st.selectbox(
            "Choose from predefined queries:",
            options=query_options,
            key="query_selector"
        )
        
        # Get selected query object
        selected_query = None
        if selected_query_title != "Select a predefined query...":
            selected_query = next(
                (q for q in predefined_queries if q.title == selected_query_title), 
                None
            )
        
        # Custom query section
        st.markdown("**Custom query**")
        custom_query = st.text_area(
            "Enter your custom query:",
            value=st.session_state.get('custom_query', ''),
            height=100,
            placeholder="Type your custom legal document query here...",
            key="custom_query_input"
        )
        
        # Client selection
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("**Client name**")
            clients = backend.get_clients()
            selected_client = st.selectbox(
                "Select client filter:",
                options=clients,
                index=clients.index(st.session_state.get('selected_client', 'All')),
                key="client_selector"
            )
        
        with col2:
            st.markdown("**Search action**")
            search_button = st.button(
                "🔍 Run",
                type="primary",
                use_container_width=True,
                key="search_button"
            )
    
    # Determine which query to use
    final_query = None
    if custom_query.strip():
        final_query = custom_query.strip()
    elif selected_query:
        final_query = selected_query.query_text
    
    # Execute search
    if search_button:
        if final_query:
            with st.spinner("Searching documents..."):
                # Update session state
                st.session_state.custom_query = custom_query
                st.session_state.selected_client = selected_client
                
                # Perform search
                search_results = backend.search_documents(
                    query=final_query,
                    client_filter=selected_client if selected_client != "All" else None
                )
                st.session_state.search_results = search_results
        else:
            st.error("Please enter a custom query or select a predefined query.")
      # Display search results
    if 'search_results' in st.session_state and st.session_state.search_results:
        results = st.session_state.search_results
        
        st.markdown("---")
        st.markdown("### Search results")
        
        # Results summary
        display_search_summary(
            results.summary,
            results.total_documents,
            results.processing_time
        )
        
        st.markdown("---")
        
        # Document snippets section
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
      # Show query information if available
    if selected_query:
        with st.expander("ℹ️ Query information"):
            st.markdown(f"**Category:** {selected_query.category}")
            st.markdown(f"**Description:** {selected_query.description}")
            st.markdown(f"**Query text:** {selected_query.query_text}")
