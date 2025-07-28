import streamlit as st
from typing import Optional, List
from backend.models import DocumentSnippet

def setup_page_config():
    st.set_page_config(
        page_title="Legal Document Search",
        page_icon="📋",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    st.markdown("""
    <style>
    .stAppHeader { display: none; }
    .stSidebar { display: none; }
    .stAppDeployButton { display: none; }
    .stApp > header { display: none; }
    
    .search-header {
        background: linear-gradient(90deg, #1f77b4, #2ca02c);
        color: white;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 2rem;
        text-align: center;
    }
    
    .search-header h1 {
        margin: 0;
        font-size: 2rem;
        font-weight: bold;
    }
    
    .document-snippet {
        background-color: #ffffff;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #e1e5e9;
        margin-bottom: 1rem;
    }
    </style>
    """, unsafe_allow_html=True)

def display_document_snippet(snippet: DocumentSnippet, index: int):
    st.markdown(f"""
    <div class="document-snippet">
        <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 0.75rem;">
            <div style="flex: 1;">
                <h4 style="margin: 0 0 0.5rem 0; color: #1f2937;">{snippet.title}</h4>
                <div style="display: flex; gap: 1rem; color: #6b7280; font-size: 0.875rem;">
                    <span><strong>Source:</strong> {snippet.source}</span>
                    <span><strong>Document type:</strong> {snippet.section or 'N/A'}</span>
                    <span><strong>Distance:</strong> {snippet.metadata.get('distance', 'N/A') if snippet.metadata else 'N/A'}</span>
                </div>
            </div>
            <div style="min-width: 80px; text-align: center;">
                <div style="background-color: #3b82f6; color: white; padding: 0.25rem 0.5rem; border-radius: 0.375rem; font-size: 0.875rem; font-weight: bold;">
                    {snippet.relevance_score:.3f}
                </div>
                <div style="font-size: 0.75rem; color: #6b7280; margin-top: 0.25rem;">Relevance</div>
            </div>
        </div>
        <p style="margin: 0 0 1rem 0; color: #374151; line-height: 1.5;">
            {snippet.content[:300] + "..." if len(snippet.content) > 300 else snippet.content}
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        if st.button(f"📄 View full document", key=f"view_doc_{index}", use_container_width=True):
            from utils.session_state import set_selected_document
            set_selected_document(snippet.id)
            st.rerun()
    
    with col2:
        presigned_url = None
        if snippet.metadata and 'presigned_url' in snippet.metadata:
            presigned_url = snippet.metadata['presigned_url']
        
        if presigned_url:
            st.markdown(f"""
            <a href="{presigned_url}" target="_blank" style="text-decoration: none;">
                <button style="
                    width: 100%;
                    padding: 0.5rem 1rem;
                    background-color: #10b981;
                    color: white;
                    border: none;
                    border-radius: 0.375rem;
                    font-weight: 500;
                    cursor: pointer;
                    transition: all 0.2s;
                " onmouseover="this.style.backgroundColor='#059669'" onmouseout="this.style.backgroundColor='#10b981'">
                    📥 Download file
                </button>
            </a>
            """, unsafe_allow_html=True)
        else:
            st.button("📥 File unavailable", disabled=True, key=f"file_unavailable_{index}", use_container_width=True)
    
    st.markdown("---")

def display_search_summary(summary: str, total_docs: int, processing_time: float):
    st.markdown("### 🤖 AI Answer")
    st.markdown(f"""
    <div style="
        background-color: #f0f9ff;
        border: 1px solid #0ea5e9;
        border-radius: 0.5rem;
        padding: 1rem;
        margin-bottom: 1rem;
    ">
        <div style="color: #374151; line-height: 1.6;">
            {summary}
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Documents found", total_docs)
    
    with col2:
        st.metric("Processing time", f"{processing_time:.2f}s")
    
    with col3:
        st.metric("Search status", "✅ Complete")

def create_info_box(title: str, content: str, type: str = "info"):
    if type == "info":
        st.info(f"**{title}**\n\n{content}")
    elif type == "warning":
        st.warning(f"**{title}**\n\n{content}")
    elif type == "error":
        st.error(f"**{title}**\n\n{content}")
    elif type == "success":
        st.success(f"**{title}**\n\n{content}")
