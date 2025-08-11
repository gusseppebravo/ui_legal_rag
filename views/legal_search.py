import streamlit as st
import pandas as pd
from typing import Optional
from backend.models import SearchResult
from utils.ui_components import display_document_snippet, display_search_summary, create_info_box, display_search_debug_info
from utils.session_state import clear_search_results

def _markdown_table_to_dataframe(markdown_table: str) -> pd.DataFrame:
    """Convert markdown table to pandas dataframe"""
    try:
        lines = markdown_table.strip().split('\n')
        lines = [line.strip() for line in lines if line.strip()]
        
        # Filter out separator lines (contain only |, -, and spaces)
        clean_lines = []
        for line in lines:
            clean_content = line.replace('|', '').replace('-', '').replace(' ', '')
            if clean_content:  # Keep lines that have actual content
                clean_lines.append(line)
        
        if len(clean_lines) < 2:
            return pd.DataFrame({'Error': ['Invalid table format']})
        
        # Parse header
        header = [col.strip() for col in clean_lines[0].split('|')[1:-1]]
        
        # Parse data rows
        data = []
        for line in clean_lines[1:]:
            row = [col.strip() for col in line.split('|')[1:-1]]
            if len(row) == len(header):
                data.append(row)
        
        return pd.DataFrame(data, columns=header)
    except Exception as e:
        return pd.DataFrame({'Error': [f'Failed to parse table: {str(e)}']})

def _style_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Apply color styling to dataframe rows based on answer column"""
    def color_rows(row):
        answer = str(row.get('Answer', '')).lower()
        
        if 'no' in answer and ('yes' not in answer or answer.strip() == 'no'):
            return ['background-color: #fee2e2'] * len(row)  # Light red
        elif 'yes' in answer and ('limitation' in answer or 'limited' in answer or 'with' in answer):
            return ['background-color: #fed7aa'] * len(row)  # Light orange
        elif 'yes' in answer:
            return ['background-color: #dcfce7'] * len(row)  # Light green
        else:
            return [''] * len(row)  # No styling
    
    return df.style.apply(color_rows, axis=1)

def _run_all_questions_search(backend, selected_clients, selected_doc_type, selected_account_type, 
                             selected_solution_line, selected_related_product, num_results):
    """Run all predefined questions against selected clients"""
    import time
    start_time = time.time()
    
    predefined_queries = backend.get_predefined_queries()
    all_results = {}
    all_search_results = {}  # Store full search results for chunk access
    
    for query_obj in predefined_queries:
        query = query_obj.query_text
        client_answers = {}
        client_search_results = {}
        
        for client in selected_clients:
            try:
                # Use the same search_documents method to ensure consistency
                search_result = backend.search_documents(
                    query=query,
                    client_filter=client,
                    document_type_filter=selected_doc_type if selected_doc_type != "All" else None,
                    account_type_filter=selected_account_type if selected_account_type != "All" else None,
                    solution_line_filter=selected_solution_line if selected_solution_line != "All" else None,
                    related_product_filter=selected_related_product if selected_related_product != "All" else None,
                    top_k=num_results
                )
                
                # Extract simple answer from full response
                simple_answer = _extract_simple_answer(search_result.summary or "No answer")
                client_answers[client] = simple_answer
                client_search_results[client] = search_result
                
            except Exception as e:
                print(f"Error processing {query_obj.title} for {client}: {e}")
                client_answers[client] = "Error"
                client_search_results[client] = None
        
        all_results[query_obj.title] = client_answers
        all_search_results[query_obj.title] = client_search_results
    
    total_time = time.time() - start_time
    return all_results, all_search_results, total_time

def _extract_simple_answer(full_answer: str) -> str:
    """Extract simple Yes/No/Yes with limitations answer from full response"""
    answer_lower = full_answer.lower()
    
    if any(phrase in answer_lower for phrase in ["yes", "allowed", "permitted", "can"]):
        if any(phrase in answer_lower for phrase in ["limitation", "restriction", "condition", "but", "however", "except"]):
            return "Yes with limitations"
        return "Yes"
    elif any(phrase in answer_lower for phrase in ["no", "not allowed", "prohibited", "cannot", "forbidden"]):
        return "No"
    else:
        return "Unclear"

def _create_questions_matrix_dataframe(all_results: dict, selected_clients: list) -> pd.DataFrame:
    """Create dataframe from all questions results"""
    data = []
    for question, client_answers in all_results.items():
        row = {"Question": question}
        for client in selected_clients:
            row[client] = client_answers.get(client, "No data")
        data.append(row)
    
    return pd.DataFrame(data)

def _style_questions_matrix(df: pd.DataFrame) -> pd.DataFrame:
    """Apply color styling to questions matrix dataframe"""
    def color_cell(val):
        val_lower = str(val).lower()
        if 'no' in val_lower and 'yes' not in val_lower:
            return 'background-color: #fee2e2'  # Light red
        elif 'yes' in val_lower and ('limitation' in val_lower or 'limited' in val_lower):
            return 'background-color: #fed7aa'  # Light orange
        elif 'yes' in val_lower:
            return 'background-color: #dcfce7'  # Light green
        else:
            return ''  # No styling
    
    # Apply styling to all columns except Question
    styled_cols = [col for col in df.columns if col != 'Question']
    return df.style.applymap(color_cell, subset=styled_cols)

def show_legal_search_page():
    from utils.session_state import has_selected_document
    if has_selected_document():
        st.info("📄 Document selected - use sidebar to view")
    
    backend = st.session_state.backend
    
    # Get filter values from sidebar (now managed in app.py)
    selected_account_type = st.session_state.get('account_type_selector', 'Client')
    selected_doc_type = st.session_state.get('doc_type_selector', 'All')
    selected_clients = st.session_state.get('client_selector', [])
    selected_solution_line = st.session_state.get('solution_line_selector', 'All')
    selected_related_product = st.session_state.get('related_product_selector', 'All')
    num_results = st.session_state.get('num_results', 5)
    min_relevance = st.session_state.get('min_relevance', 0.0)
    
    # Main content area - query selection and search
    st.markdown("**Query selection**")
    
    predefined_queries = backend.get_predefined_queries()
    query_options = ["All questions"] + [q.query_text for q in predefined_queries]
    
    selected_query_text = st.selectbox(
        "Predefined queries:",
        options=query_options,
        key="query_selector",
        label_visibility="collapsed"
    )
    
    selected_query = None
    run_all_questions = False
    
    if selected_query_text == "All questions":
        run_all_questions = True
    else:
        selected_query = next(
            (q for q in predefined_queries if q.query_text == selected_query_text),
            None
        )
    
    custom_query = st.text_area(
        "Or enter custom query:",
        value=st.session_state.get('custom_query', ''),
        height=60,
        placeholder="Type your custom legal document query here...",
        key="custom_query_input"
    )

    # Compact search button with better styling
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        search_button = st.button(
            "Search documents",
            type="secondary",
            use_container_width=True,
            key="search_button",
            icon=":material/search:"
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
        if (run_all_questions or final_query) and selected_clients:
            with st.spinner("Searching documents..."):
                st.session_state.custom_query = custom_query
                st.session_state.selected_clients = selected_clients
                st.session_state.selected_doc_type = selected_doc_type
                st.session_state.selected_account_type = selected_account_type
                st.session_state.selected_solution_line = selected_solution_line or 'All'
                st.session_state.selected_related_product = selected_related_product or 'All'
                
                if run_all_questions:
                    # Run all questions
                    all_results, all_search_results, total_time = _run_all_questions_search(
                        backend, selected_clients, selected_doc_type, selected_account_type,
                        selected_solution_line, selected_related_product, num_results
                    )
                    
                    st.session_state.all_questions_results = {
                        'results': all_results,
                        'search_results': all_search_results,
                        'clients': selected_clients,
                        'processing_time': total_time
                    }
                    st.session_state.search_results = None
                    st.session_state.multi_search_results = None
                    
                elif len(selected_clients) > 1:
                    # Multi-client search
                    multi_results = backend.search_multiple_clients(
                        query=final_query,
                        client_filters=selected_clients,
                        document_type_filter=selected_doc_type if selected_doc_type != "All" else None,
                        account_type_filter=selected_account_type if selected_account_type != "All" else None,
                        solution_line_filter=selected_solution_line if selected_solution_line != "All" else None,
                        related_product_filter=selected_related_product if selected_related_product != "All" else None,
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
                        account_type_filter=selected_account_type if selected_account_type != "All" else None,
                        solution_line_filter=selected_solution_line if selected_solution_line != "All" else None,
                        related_product_filter=selected_related_product if selected_related_product != "All" else None,
                        top_k=num_results,
                        min_relevance=min_relevance
                    )
                    st.session_state.search_results = search_results
                    st.session_state.multi_search_results = None
                
                # Log the search operation
                try:
                    from utils.usage_logger import log_search, log_predefined_query_usage
                    if run_all_questions:
                        # Skip logging for all questions mode
                        pass
                    elif len(selected_clients) > 1:
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
                if run_all_questions:
                    # Skip search history for all questions mode
                    pass
                elif len(selected_clients) > 1:
                    add_to_search_history(
                        final_query,
                        ", ".join(selected_clients),
                        selected_doc_type,
                        selected_account_type,
                        selected_solution_line,
                        selected_related_product,
                        len(selected_clients),
                        multi_results.total_processing_time
                    )
                else:
                    add_to_search_history(
                        final_query,
                        selected_clients[0] if selected_clients else "None",
                        selected_doc_type,
                        selected_account_type,
                        selected_solution_line,
                        selected_related_product,
                        search_results.total_documents,
                        search_results.processing_time
                    )
        else:
            if not run_all_questions and not final_query:
                st.error("Please enter a custom query, select a predefined query, or choose 'All questions'.")
            if not selected_clients:
                st.error("Please select at least one client.")

    # Display results - handle all three types
    if 'all_questions_results' in st.session_state and st.session_state.all_questions_results:
        # All questions results
        all_q_results = st.session_state.all_questions_results
        
        st.markdown("---")
        st.markdown("### Answers")
        
        df = _create_questions_matrix_dataframe(all_q_results['results'], all_q_results['clients'])
        styled_df = _style_questions_matrix(df)
        st.dataframe(styled_df, use_container_width=True, hide_index=True)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Questions analyzed", len(all_q_results['results']))
        with col2:
            st.metric("Clients analyzed", len(all_q_results['clients']))
        with col3:
            st.metric("Total processing time", f"{all_q_results['processing_time']:.2f}s")

        # Add expandable section for detailed results
        if 'search_results' in all_q_results and all_q_results['search_results']:
            with st.expander("📄 Detailed results with document chunks", expanded=False):
                question_tabs = st.tabs(list(all_q_results['search_results'].keys()))
                
                for i, (question, client_results) in enumerate(all_q_results['search_results'].items()):
                    with question_tabs[i]:
                        st.markdown(f"**{question}**")
                        
                        client_subtabs = st.tabs(all_q_results['clients'])
                        for j, client in enumerate(all_q_results['clients']):
                            with client_subtabs[j]:
                                search_result = client_results.get(client)
                                if search_result and search_result.snippets:
                                    st.markdown(f"**AI Answer:** {search_result.summary}")
                                    st.markdown(f"**Document snippets ({len(search_result.snippets)}):**")
                                    
                                    for idx, snippet in enumerate(search_result.snippets):
                                        display_document_snippet(snippet, f"all_q_{question}_{client}_{idx}")
                                else:
                                    st.info("No document snippets found for this client and question.")
    
    elif 'search_results' in st.session_state and st.session_state.search_results:
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
            st.session_state.get('selected_account_type', 'All'),
            st.session_state.get('selected_solution_line', 'All'),
            st.session_state.get('selected_related_product', 'All'),
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
        df = _markdown_table_to_dataframe(multi_results.tabular_summary)
        styled_df = _style_dataframe(df)
        st.dataframe(styled_df, use_container_width=True, hide_index=True)
        
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
