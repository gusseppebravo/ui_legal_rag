import streamlit as st
import pandas as pd
import time
from typing import Optional
from backend.models import SearchResult
from utils.ui_components import display_document_snippet, display_search_summary, create_info_box, display_search_debug_info
from utils.session_state import clear_search_results
from utils.interactive_table import _display_dialog_matrix_table, _create_transposed_questions_matrix_dataframe, _style_transposed_questions_matrix, _get_column_config_for_interactive_table

def _markdown_table_to_dataframe(markdown_table: str) -> pd.DataFrame:
    """Convert markdown table to pandas dataframe"""
    try:
        lines = markdown_table.strip().split('\n')
        lines = [line.strip() for line in lines if line.strip()]
        
        clean_lines = []
        for line in lines:
            clean_content = line.replace('|', '').replace('-', '').replace(' ', '')
            if clean_content:
                clean_lines.append(line)
        
        if len(clean_lines) < 2:
            return pd.DataFrame({'Error': ['Invalid table format']})
        
        header = [col.strip() for col in clean_lines[0].split('|')[1:-1]]
        
        data = []
        for line in clean_lines[1:]:
            row = [col.strip() for col in line.split('|')[1:-1]]
            if len(row) == len(header):
                data.append(row)
        
        return pd.DataFrame(data, columns=header)
    except Exception as e:
        return pd.DataFrame({'Error': [f'Failed to parse table: {str(e)}']})

def _create_single_question_matrix_dataframe(search_results_dict: dict, query: str, selected_clients: list) -> pd.DataFrame:
    """Create matrix dataframe for single question with multiple clients"""
    data = []
    for client in selected_clients:
        search_result = search_results_dict.get(client)
        if search_result:
            simple_answer = _extract_simple_answer(search_result.summary or "No answer")
        else:
            simple_answer = "No data"
        
        row = {
            "Account": client,
            query: simple_answer
        }
        data.append(row)
    
    return pd.DataFrame(data)

def _run_all_questions_search(backend, selected_clients, selected_doc_type, selected_account_type, 
                             selected_solution_line, selected_related_product, num_results):
    """Run all predefined questions against selected clients"""
    start_time = time.time()
    
    predefined_queries = backend.get_predefined_queries()
    all_results = {}
    all_search_results = {}
    
    for query_obj in predefined_queries:
        query = query_obj.query_text
        client_answers = {}
        client_search_results = {}
        
        for client in selected_clients:
            try:
                search_result = backend.search_documents(
                    query=query,
                    client_filter=client,
                    document_type_filter=selected_doc_type if selected_doc_type != "All" else None,
                    account_type_filter=selected_account_type if selected_account_type != "All" else None,
                    solution_line_filter=selected_solution_line if selected_solution_line != "All" else None,
                    related_product_filter=selected_related_product if selected_related_product != "All" else None,
                    top_k=num_results
                )
                
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
    """Extract simple Yes/No/Maybe answer from full response"""
    answer_lower = full_answer.lower()
    
    if any(phrase in answer_lower for phrase in ["yes", "allowed", "permitted", "can"]):
        if any(phrase in answer_lower for phrase in ["limitation", "restriction", "condition", "but", "however", "except"]):
            return "Maybe"
        return "Yes"
    elif any(phrase in answer_lower for phrase in ["no", "not allowed", "prohibited", "cannot", "forbidden"]):
        return "No"
    else:
        return "Unclear"



def show_legal_search_page():
    from utils.session_state import has_selected_document
    if has_selected_document():
        st.info("📄 Document selected - use sidebar to view")
    
    backend = st.session_state.backend
    
    selected_account_type = st.session_state.get('account_type_selector', 'Client')
    selected_doc_type = st.session_state.get('doc_type_selector', 'All')
    selected_clients = st.session_state.get('client_selector', [])
    selected_solution_line = st.session_state.get('solution_line_selector', 'All')
    selected_related_product = st.session_state.get('related_product_selector', 'All')
    num_results = st.session_state.get('num_results', 5)
    min_relevance = st.session_state.get('min_relevance', 0.0)
    
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

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        search_button = st.button(
            "Search documents",
            type="secondary",
            use_container_width=True,
            key="search_button",
            icon=":material/search:"
        )

    final_query = None
    
    if custom_query.strip():
        final_query = custom_query.strip()
        run_all_questions = False
        if selected_query_text == "All questions":
            st.info("📝 Using custom query. 'All questions' selection will be ignored.")
        elif selected_query and selected_query_text != "Select predefined query...":
            st.info("📝 Using custom query. Predefined query will be ignored.")
    elif selected_query and selected_query_text != "Select predefined query...":
        final_query = selected_query.query_text
    
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
                    st.session_state.all_questions_results = None
                else:
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
                    # Create a unified structure like multi_search_results for consistency
                    class SingleQueryResult:
                        def __init__(self, query, client_search_results):
                            self.query = query
                            self.client_search_results = client_search_results
                            # Create a simple tabular summary for single client
                            if client_search_results:
                                client_name = list(client_search_results.keys())[0]
                                client_result = client_search_results[client_name]
                                simple_answer = _extract_simple_answer(client_result.summary if client_result else "No answer")
                                self.tabular_summary = f"| Client | Answer |\n|--------|--------|\n| {client_name} | {simple_answer} |"
                            else:
                                self.tabular_summary = "No results available"
                    
                    multi_results = SingleQueryResult(
                        query=final_query,
                        client_search_results={single_client: search_results}
                    )
                    st.session_state.multi_search_results = multi_results
                    st.session_state.search_results = None
                    st.session_state.all_questions_results = None
                
                try:
                    from utils.usage_logger import log_search, log_predefined_query_usage
                    if run_all_questions:
                        log_search(
                            query="[ALL QUESTIONS]",
                            client_filter=", ".join(selected_clients),
                            doc_type_filter=selected_doc_type if selected_doc_type != "All" else None,
                            account_type_filter=selected_account_type if selected_account_type != "All" else None,
                            solution_line_filter=selected_solution_line if selected_solution_line != "All" else None,
                            related_product_filter=selected_related_product if selected_related_product != "All" else None,
                            result_count=len(all_results),
                            processing_time=total_time,
                            search_type="all_questions"
                        )
                    elif len(selected_clients) > 1:
                        log_search(
                            query=final_query,
                            client_filter=", ".join(selected_clients),
                            doc_type_filter=selected_doc_type if selected_doc_type != "All" else None,
                            account_type_filter=selected_account_type if selected_account_type != "All" else None,
                            solution_line_filter=selected_solution_line if selected_solution_line != "All" else None,
                            related_product_filter=selected_related_product if selected_related_product != "All" else None,
                            result_count=len(selected_clients),
                            processing_time=multi_results.total_processing_time,
                            search_type="multi"
                        )
                    else:
                        # For single client, extract from multi_results structure
                        single_client_key = list(multi_results.client_search_results.keys())[0]
                        single_search_result = multi_results.client_search_results[single_client_key]
                        log_search(
                            query=final_query,
                            client_filter=single_client_key,
                            doc_type_filter=selected_doc_type if selected_doc_type != "All" else None,
                            account_type_filter=selected_account_type if selected_account_type != "All" else None,
                            solution_line_filter=selected_solution_line if selected_solution_line != "All" else None,
                            related_product_filter=selected_related_product if selected_related_product != "All" else None,
                            result_count=single_search_result.total_documents,
                            processing_time=single_search_result.processing_time,
                            search_type="single"
                        )
                    
                    if selected_query:
                        log_predefined_query_usage(selected_query.id, selected_query.title)
                except Exception:
                    pass
                
                from utils.session_state import add_to_search_history
                if run_all_questions:
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
                    # For single client, extract from multi_results structure
                    single_client_key = list(multi_results.client_search_results.keys())[0]
                    single_search_result = multi_results.client_search_results[single_client_key]
                    add_to_search_history(
                        final_query,
                        single_client_key,
                        selected_doc_type,
                        selected_account_type,
                        selected_solution_line,
                        selected_related_product,
                        single_search_result.total_documents,
                        single_search_result.processing_time
                    )
        else:
            if not run_all_questions and not final_query:
                st.error("Please enter a custom query, select a predefined query, or choose 'All questions'.")
            if not selected_clients:
                st.error("Please select at least one client.")

    # Display results
    if 'all_questions_results' in st.session_state and st.session_state.all_questions_results:
        all_q_results = st.session_state.all_questions_results
        
        st.markdown("---")
        st.markdown("### Answers")
        
        df = _create_transposed_questions_matrix_dataframe(all_q_results['results'], all_q_results['clients'])
        styled_df = _style_transposed_questions_matrix(df)
        # st.dataframe(styled_df, use_container_width=True, hide_index=True)
        
        # with st.expander("### Details and feedback", expanded=False):
        _display_dialog_matrix_table(df, all_questions_results=all_q_results)
        
        # col1, col2, col3 = st.columns(3)
        # with col1:
        #     st.metric("Questions analyzed", len(all_q_results['results']))
        # with col2:
        #     st.metric("Clients analyzed", len(all_q_results['clients']))
        # with col3:
        #     st.metric("Total processing time", f"{all_q_results['processing_time']:.2f}s")
    
    elif 'multi_search_results' in st.session_state and st.session_state.multi_search_results:
        multi_results = st.session_state.multi_search_results
        
        st.markdown("---")
        st.markdown("### Answer")
        
        # Both single and multiple clients use the same matrix format
        if hasattr(multi_results, 'client_search_results') and multi_results.client_search_results:
            client_results_dict = multi_results.client_search_results
            query = multi_results.query
            clients = list(client_results_dict.keys())
            
            df = _create_single_question_matrix_dataframe(client_results_dict, query, clients)
            styled_df = _style_transposed_questions_matrix(df)
            # st.dataframe(styled_df, use_container_width=True, hide_index=True)
            
            # with st.expander("### Details and feedback", expanded=False):
            _display_dialog_matrix_table(df, search_results=multi_results)
        else:
            # Fallback to original table format
            df = _markdown_table_to_dataframe(multi_results.tabular_summary)
            # st.dataframe(df, use_container_width=True, hide_index=True)
            
            # with st.expander("### Details and feedback", expanded=False):
            _display_dialog_matrix_table(df, search_results=multi_results)