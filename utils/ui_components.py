"""
UI components and styling utilities
"""

import streamlit as st
from typing import Optional, List
from backend.models import DocumentSnippet

def setup_page_config():
    """Setup Streamlit page configuration"""
    st.set_page_config(
        page_title="Legal Document Search",
        page_icon="📋",
        layout="wide",
        initial_sidebar_state="collapsed",
        menu_items={
            'Get Help': None,
            'Report a bug': None,
            'About': None
        }
    )
    # Apply custom CSS
    st.markdown("""
    <style>
    /* Hide Streamlit's default navigation elements */
    .stAppHeader {
        display: none;
    }
    
    .stAppViewContainer > .main > div:nth-child(1) > div:nth-child(1) {
        display: none;
    }
    
    /* Hide the sidebar completely */
    .stSidebar {
        display: none;
    }
    
    .stAppViewContainer .main .block-container {
        padding-left: 1rem;
        padding-right: 1rem;
        max-width: none;
    }
    
    /* Hide the top navigation bar */
    .stAppDeployButton {
        display: none;
    }
    
    /* Hide any default Streamlit branding */
    .stApp > header {
        display: none;
    }
    
    /* Hide the "Made with Streamlit" footer */
    .stApp > footer {
        display: none;
    }
    
    /* Hide the hamburger menu */
    .stActionButton {
        display: none;
    }
    
    .main {
        padding-top: 1rem;
    }
    
    .stSelectbox > div > div > select {
        background-color: #f8f9fa;
    }
    
    .stTextInput > div > div > input {
        background-color: #f8f9fa;
    }
    
    .stTextArea > div > div > textarea {
        background-color: #f8f9fa;
    }
    
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    
    .document-snippet {
        background-color: #ffffff;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #e1e5e9;
        margin-bottom: 1rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .search-header {
        background: linear-gradient(90deg, #1f77b4, #2ca02c);
        color: white;
        padding: 1.5rem;
        border-radius: 0.5rem;
        margin-bottom: 2rem;
        text-align: center;
    }
    
    .search-header h1 {
        margin: 0;
        font-size: 2rem;
        font-weight: bold;
    }
    
    .concept-badge {
        display: inline-block;
        padding: 0.25rem 0.5rem;
        margin: 0.125rem;
        border-radius: 0.25rem;
        color: white;
        font-weight: bold;
        font-size: 0.875rem;
    }
    
    .sidebar .sidebar-content {
        padding-top: 1rem;
    }
    
    .stButton > button {
        border-radius: 0.375rem;
        border: 1px solid #d1d5db;
        background-color: white;
        padding: 0.5rem 1rem;
        font-weight: 500;
        transition: all 0.2s;
    }
    
    .stButton > button:hover {
        background-color: #f9fafb;
        border-color: #9ca3af;
    }
    
    .stButton > button[kind="primary"] {
        background-color: #3b82f6;
        border-color: #3b82f6;
        color: white;
    }
    
    .stButton > button[kind="primary"]:hover {
        background-color: #2563eb;
        border-color: #2563eb;
    }
    </style>
    """, unsafe_allow_html=True)

def display_document_snippet(snippet: DocumentSnippet, index: int):
    """Display a document snippet with click functionality"""
    
    # Create a styled container for the snippet
    st.markdown(f"""
    <div class="document-snippet">
        <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 0.75rem;">
            <div style="flex: 1;">
                <h4 style="margin: 0 0 0.5rem 0; color: #1f2937;">{snippet.title}</h4>
                <div style="display: flex; gap: 1rem; color: #6b7280; font-size: 0.875rem;">
                    <span><strong>Source:</strong> {snippet.source}</span>
                    <span><strong>Page:</strong> {snippet.page_number}</span>
                    <span><strong>Section:</strong> {snippet.section}</span>
                </div>
            </div>
            <div style="min-width: 80px; text-align: center;">
                <div style="background-color: #3b82f6; color: white; padding: 0.25rem 0.5rem; border-radius: 0.375rem; font-size: 0.875rem; font-weight: bold;">
                    {snippet.relevance_score:.2f}
                </div>
                <div style="font-size: 0.75rem; color: #6b7280; margin-top: 0.25rem;">Relevance</div>
            </div>
        </div>
        <p style="margin: 0 0 1rem 0; color: #374151; line-height: 1.5;">
            {snippet.content[:200] + "..." if len(snippet.content) > 200 else snippet.content}
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Click to view full document
    if st.button(f"📄 View Full Document", key=f"view_doc_{index}", use_container_width=True):
        from utils.session_state import set_selected_document
        set_selected_document(snippet.id)
        st.rerun()
    
    st.markdown("---")

def display_search_summary(summary: str, total_docs: int, processing_time: float):
    """Display search results summary"""
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Result Summary", summary)
    
    with col2:
        st.metric("Documents Found", total_docs)
    
    with col3:
        st.metric("Processing Time", f"{processing_time:.2f}s")

def display_loading_spinner(message: str = "Processing..."):
    """Display a loading spinner with message"""
    with st.spinner(message):
        return st.empty()

def create_info_box(title: str, content: str, type: str = "info"):
    """Create an info box with specified type"""
    if type == "info":
        st.info(f"**{title}**\n\n{content}")
    elif type == "warning":
        st.warning(f"**{title}**\n\n{content}")
    elif type == "error":
        st.error(f"**{title}**\n\n{content}")
    elif type == "success":
        st.success(f"**{title}**\n\n{content}")

def style_metric_cards():
    """Apply custom CSS for metric cards"""
    st.markdown("""
    <style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    
    .document-snippet {
        background-color: #ffffff;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #e1e5e9;
        margin-bottom: 1rem;
    }
    
    .search-header {
        background: linear-gradient(90deg, #1f77b4, #2ca02c);
        color: white;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 2rem;
    }
    </style>
    """, unsafe_allow_html=True)
