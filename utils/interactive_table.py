import streamlit as st
import pandas as pd
from typing import Optional
from utils.ui_components import display_document_snippet


def _get_answer_background_color(answer: str) -> str:
    """Get background color for answer based on content"""
    answer_lower = str(answer).lower()
    if 'no' in answer_lower and ('yes' not in answer_lower or answer_lower.strip() == 'no'):
        return '#fee2e2'
    elif 'yes' in answer_lower and ('limitation' in answer_lower or 'limited' in answer_lower or 'with' in answer_lower):
        return '#fed7aa'
    elif 'yes' in answer_lower:
        return '#dcfce7'
    else:
        return '#f8f9fa'


def _transpose_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Transpose dataframe swapping rows and columns; expects first column to be questions."""
    if 'Question' in df.columns:
        transposed_data = []
        question_col = df['Question'].tolist()
        client_cols = [col for col in df.columns if col != 'Question']
        for client in client_cols:
            row = {'Account': client}
            for i, question in enumerate(question_col):
                row[question] = df.iloc[i][client]
            transposed_data.append(row)
        return pd.DataFrame(transposed_data)
    else:
        return df


def _style_transposed_questions_matrix(df: pd.DataFrame) -> pd.DataFrame:
    """Apply color styling to transposed questions matrix dataframe"""
    def color_cell(val):
        val_lower = str(val).lower()
        if 'no' in val_lower and 'yes' not in val_lower:
            return 'background-color: #fee2e2; color: #7f1d1d; font-weight: 500;'
        elif 'yes' in val_lower and ('limitation' in val_lower or 'limited' in val_lower):
            return 'background-color: #fed7aa; color: #9a3412; font-weight: 500;'
        elif 'yes' in val_lower:
            return 'background-color: #dcfce7; color: #166534; font-weight: 500;'
        else:
            return 'color: #374151; font-weight: 500;'
    styled_cols = [col for col in df.columns if col != 'Account']
    return df.style.map(color_cell, subset=styled_cols)


@st.dialog("Answer details")
def _show_answer_dialog(question: str, answer: str, search_results=None, client=None, all_questions_results=None):
    """Dialog showing answer, details and feedback for a single answer cell."""
    bg_color = _get_answer_background_color(answer)
    st.markdown(f"""
    <div style="background-color: {bg_color}; border-radius: 0.5rem; padding: 1rem; margin-bottom: 1rem; border: 1px solid #e5e7eb; color: black;">
        <strong>Answer:</strong> {answer}
    </div>
    """, unsafe_allow_html=True)

    with st.expander("More details", expanded=True):
        # details
        with st.expander("📄 Details", expanded=False):
            if search_results:
                if hasattr(search_results, 'summary'):
                    st.markdown("**Full AI answer:**")
                    st.write(search_results.summary)
                    if hasattr(search_results, 'snippets') and search_results.snippets:
                        st.markdown(f"**Document snippets ({len(search_results.snippets)}):**")
                        for idx, snippet in enumerate(search_results.snippets):
                            display_document_snippet(snippet, f"dialog_single_{idx}")
                    else:
                        st.info("No document snippets available")
                elif hasattr(search_results, 'client_search_results') and search_results.client_search_results:
                    # Handle multi-client results with tabular_summary
                    if hasattr(search_results, 'tabular_summary'):
                        st.markdown("**Full summary:**")
                        st.write(search_results.tabular_summary)
                    
                    # Show individual client details
                    st.markdown("**Document sources:**")
                    for client_name, client_result in search_results.client_search_results.items():
                        st.markdown(f"**{client_name}:**")
                        if client_result and client_result.snippets:
                            # Show full answer for this client
                            if hasattr(client_result, 'summary') and client_result.summary:
                                st.markdown("**Full AI answer:**")
                                st.write(client_result.summary)
                            # Show document snippets
                            st.markdown(f"**Document snippets ({len(client_result.snippets)}):**")
                            for i, snippet in enumerate(client_result.snippets[:3]):
                                display_document_snippet(snippet, f"dialog_multi_{client_name}_{i}")
                        else:
                            st.info(f"No document sources for {client_name}")
            elif all_questions_results and client:
                search_results_data = all_questions_results.get('search_results', {})
                if question in search_results_data and client in search_results_data[question]:
                    client_search_result = search_results_data[question][client]
                    if client_search_result and hasattr(client_search_result, 'summary'):
                        st.markdown("**Full AI answer:**")
                        st.write(client_search_result.summary)
                        if hasattr(client_search_result, 'snippets') and client_search_result.snippets:
                            st.markdown(f"**Document snippets ({len(client_search_result.snippets)}):**")
                            for idx, snippet in enumerate(client_search_result.snippets):
                                display_document_snippet(snippet, f"dialog_all_q_{question}_{client}_{idx}")
                        else:
                            st.info("No document snippets available")
                    else:
                        st.info("No detailed information available")
                else:
                    st.info("No detailed information available")
            else:
                st.info("No detailed information available")

        # feedback
        with st.expander("💬 Feedback", expanded=False):
            st.markdown("**Help us improve the system:**")
            feedback_options = [
                "Answer is accurate and helpful",
                "Answer is partially correct but incomplete",
                "Answer is incorrect or misleading",
                "Answer lacks sufficient detail",
            ]
            key_base = f"feedback_{question}_{client or 'single'}_{str(answer)[:10]}"
            selected_feedback = st.radio("Select feedback type:", options=feedback_options, key=key_base + "_radio")
            custom_feedback = st.text_area("Additional comments (optional):", placeholder="Please provide specific feedback...", height=100, key=key_base + "_text")
            col1, col2 = st.columns([1, 1])
            with col1:
                if st.button("Submit feedback", type="primary", use_container_width=True, key=key_base + "_submit"):
                    # Log feedback to usage logger
                    try:
                        from utils.usage_logger import get_usage_logger
                        logger = get_usage_logger()
                        logger.log_feedback(
                            question=question,
                            answer=answer,
                            client=client,
                            feedback_type=selected_feedback,
                            custom_feedback=custom_feedback,
                            search_context={
                                'has_search_results': search_results is not None,
                                'has_all_questions_results': all_questions_results is not None
                            }
                        )
                    except Exception:
                        pass
                    
                    if 'user_feedback' not in st.session_state:
                        st.session_state.user_feedback = {}
                    st.session_state.user_feedback[key_base] = {
                        'question': question,
                        'answer': answer,
                        'client': client,
                        'selected_feedback': selected_feedback,
                        'custom_feedback': custom_feedback,
                        'timestamp': pd.Timestamp.now()
                    }
                    st.success("✅ Feedback submitted successfully!")
                    st.rerun()
            with col2:
                if st.button("Cancel", use_container_width=True, key=key_base + "_cancel"):
                    st.rerun()


def _display_dialog_matrix_table(df: pd.DataFrame, search_results=None, all_questions_results=None):
    """Display dataframe as a matrix of dialog buttons with colored styling"""
    # Check if this is a single question/answer format (without Account column)
    if 'Account' not in df.columns and len(df.columns) == 2:
        st.markdown("**Click on any answer to view details and provide feedback:**")
        for idx, row in df.iterrows():
            question = row.get('Question', '')
            answer = row.get('Answer', '')
            if st.button(str(answer), key=f"dlg_{idx}_single_{str(answer)[:10]}", use_container_width=True):
                _show_answer_dialog(question, str(answer), search_results)
    else:
        # Matrix format with Account column
        st.markdown("**Click on any answer to view details and provide feedback:**")
        # header
        cols = st.columns(len(df.columns))
        for i, col_name in enumerate(df.columns):
            with cols[i]:
                st.markdown(f"**{col_name}**")
        # rows
        for idx, row in df.iterrows():
            cols = st.columns(len(df.columns))
            for i, (col_name, value) in enumerate(row.items()):
                with cols[i]:
                    if col_name == 'Account':
                        st.markdown(f"*{value}*")
                    else:
                        bg = _get_answer_background_color(str(value))
                        if st.button(str(value), key=f"dlg_mat_{idx}_{i}_{str(value)[:10]}", use_container_width=True):
                            _show_answer_dialog(col_name, str(value), search_results, client=row.get('Account'), all_questions_results=all_questions_results
                            )

def _create_transposed_questions_matrix_dataframe(all_results: dict, selected_clients: list) -> pd.DataFrame:
    """Create transposed dataframe from all questions results (clients as rows, questions as columns)"""
    questions = list(all_results.keys())
    
    data = []
    for client in selected_clients:
        row = {"Account": client}
        for question in questions:
            client_answers = all_results.get(question, {})
            row[question] = client_answers.get(client, "No data")
        data.append(row)
    
    return pd.DataFrame(data)

def _get_column_config_for_interactive_table(df: pd.DataFrame):
    """Create column configuration for interactive table"""
    column_config = {}
    
    if 'Question' in df.columns:
        column_config['Question'] = st.column_config.TextColumn(
            "Question",
            help="Question being asked",
            width="large"
        )
    
    if 'Answer' in df.columns:
        column_config['Answer'] = st.column_config.TextColumn(
            "Answer",
            help="AI generated answer",
            width="medium"
        )
    
    for col in df.columns:
        if col not in ['Question', 'Answer', 'Details', 'Feedback']:
            column_config[col] = st.column_config.TextColumn(
                col,
                help=f"Answer for {col}",
                width="medium"
            )
    
    if 'Details' in df.columns:
        column_config['Details'] = st.column_config.SelectboxColumn(
            "Details",
            help="View detailed information",
            width="small",
            options=[
                "View details",
                "Full summary",
                "Document sources"
            ]
        )
    
    if 'Feedback' in df.columns:
        column_config['Feedback'] = st.column_config.SelectboxColumn(
            "Feedback", 
            help="Provide feedback on this question",
            width="small",
            options=[
                "Leave feedback",
                "👍 Helpful",
                "👎 Not helpful",
                "⚠️ Incorrect", 
                "💡 Suggest improvement"
            ]
        )
    
    return column_config