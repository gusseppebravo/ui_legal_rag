import streamlit as st
from typing import Optional, List
from backend.models import DocumentSnippet

def setup_page_config():
    st.set_page_config(
        page_title="Legal RAG",
        page_icon="📋",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    st.markdown("""
    <style>
    .stAppHeader { display: none; }
    .stAppDeployButton { display: none; }
    .stApp > header { display: none; }
    
    /* Hide development/debug elements but preserve sidebar controls */
    .css-1544g2n { display: none; }
    .css-1d391kg .css-1544g2n { display: none; }
    .stSidebar .css-1544g2n { display: none; }
    .css-1dp5vir { display: none; }
    
    /* Ensure sidebar toggle button is visible */
    [data-testid="collapsedControl"] { display: block !important; }
    .css-1cypcdb { display: block !important; }
    
    /* Compact sidebar */
    .css-1d391kg { padding-top: 1rem; }
    
    /* More compact content */
    .block-container { 
        padding-top: 1rem; 
        padding-bottom: 1rem;
        max-width: 1200px;
    }
    
    /* Smaller fonts and spacing */
    .stMetric { font-size: 0.9rem; }
    .stMetric > div > div { font-size: 1.2rem !important; }
    
    /* Compact buttons */
    .stButton > button {
        padding: 0.4rem 0.8rem;
        font-size: 0.9rem;
    }
    
    .search-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 0.8rem;
        border-radius: 0.4rem;
        margin-bottom: 1rem;
        text-align: center;
    }
    
    .search-header h1 {
        margin: 0;
        font-size: 1.5rem;
        font-weight: bold;
    }
    
    .document-snippet {
        background-color: #ffffff;
        padding: 0.8rem;
        border-radius: 0.4rem;
        border: 1px solid #e1e5e9;
        margin-bottom: 0.8rem;
    }
    
    /* Compact selectbox and inputs */
    .stSelectbox > div > div { font-size: 0.9rem; }
    .stTextArea > div > div { font-size: 0.9rem; }
    
    /* Smaller section headers */
    h3 { font-size: 1.2rem; margin-bottom: 0.5rem; }
    h4 { font-size: 1.1rem; margin-bottom: 0.4rem; }
    </style>
    """, unsafe_allow_html=True)

def display_document_snippet(snippet: DocumentSnippet, index: int):
    st.markdown(f"""
    <div class="document-snippet">
        <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 0.5rem;">
            <div style="flex: 1;">
                <h4 style="margin: 0 0 0.3rem 0; color: #1f2937; font-size: 1.1rem;">{snippet.title}</h4>
                <div style="display: flex; gap: 0.8rem; color: #6b7280; font-size: 0.8rem;">
                    <span><strong>Source:</strong> {snippet.source}</span>
                    <span><strong>Type:</strong> {snippet.section or 'N/A'}</span>
                    <span><strong>Distance:</strong> {snippet.distance:.3f}</span>
                </div>
            </div>
            <div style="min-width: 70px; text-align: center;">
                <div style="background-color: #3b82f6; color: white; padding: 0.2rem 0.4rem; border-radius: 0.3rem; font-size: 0.8rem; font-weight: bold;">
                    {snippet.relevance_score:.3f}
                </div>
                <div style="font-size: 0.7rem; color: #6b7280; margin-top: 0.2rem;">Relevance</div>
            </div>
        </div>
        <p style="margin: 0 0 0.8rem 0; color: #374151; line-height: 1.4; font-size: 0.9rem;">
            {snippet.content[:250] + "..." if len(snippet.content) > 250 else snippet.content}
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Use popover instead of navigation
    with st.popover("📄 View chunk", use_container_width=True):
        # Log document view
        try:
            from .usage_logger import log_document_view
            log_document_view(snippet.id, "search_results")
        except Exception:
            pass
        
        _display_document_details(snippet)

    st.markdown("---")

def _display_document_details(snippet: DocumentSnippet):
    """Display document details in popover"""
    st.markdown(f"### {snippet.title}")
    
    # Document content
    st.markdown("**Content**")
    st.markdown(f"""
    <div style="
        background-color: #f8f9fa; 
        padding: 1rem; 
        border-radius: 0.4rem; 
        border-left: 3px solid #007bff;
        margin: 0.5rem 0;
        line-height: 1.5;
        font-size: 0.9rem;
        max-height: 300px;
        overflow-y: auto;
    ">
        {snippet.content}
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Extract metadata
    contract_number = "N/A"
    if snippet.metadata and 's3_path' in snippet.metadata:
        s3_path = snippet.metadata['s3_path']
        if '/contract-docs/' in s3_path:
            path_parts = s3_path.split('/contract-docs/')
            if len(path_parts) > 1:
                remaining_path = path_parts[1]
                contract_parts = remaining_path.split('/')
                if contract_parts:
                    contract_number = contract_parts[0]
    
    client_name = "N/A"
    if snippet.metadata:
        account_details = snippet.metadata.get("account_details", [])
        if isinstance(account_details, list) and len(account_details) > 0:
            client_name = account_details[0] if account_details[0] else "N/A"
        else:
            client_account = snippet.metadata.get("client_account", "N/A")
            if isinstance(client_account, list):
                client_name = client_account[0] if client_account else "N/A"
            else:
                client_name = client_account if client_account != "N/A" else "N/A"
    
    def format_value(value):
        if isinstance(value, list):
            return ", ".join(str(v) for v in value if v) if value else "N/A"
        return str(value) if value else "N/A"
    
    # Document details table
    st.markdown("**Document details**")
    
    metadata_rows = []
    metadata_rows.append(f"| **Client** | {client_name} |")
    metadata_rows.append(f"| **Contract** | {contract_number} |")
    metadata_rows.append(f"| **Source** | {snippet.source} |")
    metadata_rows.append(f"| **Document type** | {snippet.section or 'N/A'} |")
    metadata_rows.append(f"| **Relevance** | {snippet.relevance_score:.3f} |")
    metadata_rows.append(f"| **Distance** | {snippet.distance:.3f} |")
    
    if snippet.metadata:
        key_fields = {
            'contract_title': 'Contract title',
            'solution_line': 'Solution line', 
            'status_reason': 'Status',
            'contract_requester': 'Requester',
            'reviewing_attorney': 'Reviewing attorney',
            'created_on': 'Created date',
            'document_effective_date': 'Effective date',
            'parent_contract': 'Parent contract'
        }
        
        for field, display_name in key_fields.items():
            if field in snippet.metadata and snippet.metadata[field]:
                value = format_value(snippet.metadata[field])
                metadata_rows.append(f"| **{display_name}** | {value} |")
        
        if 'dates' in snippet.metadata and snippet.metadata['dates']:
            dates = snippet.metadata['dates']
            formatted_dates = format_value(dates)
            metadata_rows.append(f"| **Key dates** | {formatted_dates} |")
        
        if 'attorneys' in snippet.metadata and snippet.metadata['attorneys']:
            attorneys = snippet.metadata['attorneys']
            formatted_attorneys = format_value(attorneys)
            metadata_rows.append(f"| **Legal team** | {formatted_attorneys} |")
    
    table_content = "| Field | Value |\n|-------|-------|\n" + "\n".join(metadata_rows)
    st.markdown(table_content)
    
    # Download link if available
    if snippet.metadata and 'presigned_url' in snippet.metadata:
        presigned_url = snippet.metadata['presigned_url']
        if presigned_url:
            st.markdown("---")
            st.markdown(f"[📥 Download file]({presigned_url})")

def display_search_summary(summary: str, total_docs: int, processing_time: float):
    st.markdown("### 🤖 AI Answer")
    st.markdown(f"""
    <div style="
        background-color: #f0f9ff;
        border: 1px solid #0ea5e9;
        border-radius: 0.4rem;
        padding: 0.8rem;
        margin-bottom: 0.8rem;
        font-size: 0.95rem;
    ">
        <div style="color: #374151; line-height: 1.5;">
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

def display_search_debug_info(query: str, client_filter: str, document_type_filter: str, 
                             account_type_filter: str = None, solution_line_filter: str = None, 
                             related_product_filter: str = None, total_chunks: int = 0):
    with st.expander("🔍 Search details", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Query:**")
            st.text(query[:80] + "..." if len(query) > 80 else query)
            
            st.markdown("**Client filter:**")
            st.write(client_filter or "All clients")
            
            st.markdown("**Document type:**")
            st.write(document_type_filter or "All types")
        
        with col2:
            st.markdown("**Account type:**")
            st.write(account_type_filter or "All")
            
            if solution_line_filter and solution_line_filter != "All":
                st.markdown("**Solution line:**")
                st.write(solution_line_filter)
            
            if related_product_filter and related_product_filter != "All":
                st.markdown("**Related product:**")
                st.write(related_product_filter)
            
            st.markdown("**Results:**")
            st.write(f"{total_chunks} chunks")
        
        st.caption("Vector search using e5_mistral_embed_384 • AWS S3 Vector Store")
