import streamlit as st
from utils.session_state import clear_selected_document

def show_document_viewer_page():
    if 'selected_document' not in st.session_state or not st.session_state.selected_document:
        st.error("No document selected. Please go back to search and select a document.")
        return
    
    # Check for either single or multi-client search results
    has_single_results = 'search_results' in st.session_state and st.session_state.search_results
    has_multi_results = 'multi_search_results' in st.session_state and st.session_state.multi_search_results
    
    if not has_single_results and not has_multi_results:
        st.error("No search results found. Please go back and perform a search first.")
        return
    
    document_id = st.session_state.selected_document
    
    # Find the selected snippet from search results
    selected_snippet = None
    
    # First try single client search results
    if has_single_results:
        search_results = st.session_state.search_results
        for snippet in search_results.snippets:
            if snippet.id == document_id:
                selected_snippet = snippet
                break
    
    # If not found, try multi-client search results
    if not selected_snippet and has_multi_results:
        multi_results = st.session_state.multi_search_results
        if multi_results.client_search_results:
            for client, client_results in multi_results.client_search_results.items():
                for snippet in client_results.snippets:
                    if snippet.id == document_id:
                        selected_snippet = snippet
                        break
                if selected_snippet:
                    break
    
    if not selected_snippet:
        st.error("Selected document not found in search results.")
        return
    
    # Header - more compact
    col1, col2 = st.columns([5, 1])
    with col1:
        st.subheader("📄 Document Chunk")
        st.markdown(f"**{selected_snippet.title}**")
    
    with col2:
        if st.button("✖️", help="Close document", key="close_doc"):
            clear_selected_document()
            st.rerun()
    
    st.markdown("---")
    
    # Document content - immediately after title
    st.markdown("### Content")
    
    st.markdown(f"""
    <div style="
        background-color: #f8f9fa; 
        padding: 1rem; 
        border-radius: 0.4rem; 
        border-left: 3px solid #007bff;
        margin: 0.5rem 0;
        line-height: 1.5;
        font-size: 0.95rem;
    ">
        {selected_snippet.content}
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Comprehensive metadata table
    st.markdown("### 📋 Document Details")
    
    # Extract contract number from s3_path
    contract_number = "N/A"
    if selected_snippet.metadata and 's3_path' in selected_snippet.metadata:
        s3_path = selected_snippet.metadata['s3_path']
        if '/contract-docs/' in s3_path:
            # Extract number after /contract-docs/
            path_parts = s3_path.split('/contract-docs/')
            if len(path_parts) > 1:
                remaining_path = path_parts[1]
                # Get the first directory after contract-docs/
                contract_parts = remaining_path.split('/')
                if contract_parts:
                    contract_number = contract_parts[0]
    
    # Extract client name
    client_name = "N/A"
    if selected_snippet.metadata:
        client_account_details = selected_snippet.metadata.get("client_account_details", [])
        if isinstance(client_account_details, list) and len(client_account_details) > 0:
            client_name = client_account_details[0] if client_account_details[0] else "N/A"
        else:
            # Fallback to old structure if needed
            client_account = selected_snippet.metadata.get("client_account", "N/A")
            if isinstance(client_account, list):
                client_name = client_account[0] if client_account else "N/A"
            else:
                client_name = client_account if client_account != "N/A" else "N/A"
    
    # Helper function to format values
    def format_value(value):
        if isinstance(value, list):
            return ", ".join(str(v) for v in value if v) if value else "N/A"
        return str(value) if value else "N/A"
    
    # Create comprehensive metadata table
    metadata_rows = []
    
    # Basic document information
    metadata_rows.append(f"| **Client** | {client_name} |")
    metadata_rows.append(f"| **Contract** | {contract_number} |")
    metadata_rows.append(f"| **Source** | {selected_snippet.source} |")
    metadata_rows.append(f"| **Document Type** | {selected_snippet.section or 'N/A'} |")
    metadata_rows.append(f"| **Relevance** | {selected_snippet.relevance_score:.3f} |")
    metadata_rows.append(f"| **Distance** | {selected_snippet.distance:.3f} |")
    
    # Additional metadata fields if available
    if selected_snippet.metadata:
        key_fields = {
            'contract_title': 'Contract Title',
            'solution_line': 'Solution Line', 
            'status_reason': 'Status',
            'contract_requester': 'Requester',
            'reviewing_attorney': 'Reviewing Attorney',
            'created_on': 'Created Date',
            'document_effective_date': 'Effective Date',
            'parent_contract': 'Parent Contract'
        }
        
        # Add key fields if they exist
        for field, display_name in key_fields.items():
            if field in selected_snippet.metadata and selected_snippet.metadata[field]:
                value = format_value(selected_snippet.metadata[field])
                metadata_rows.append(f"| **{display_name}** | {value} |")
        
        # Add aggregated fields
        if 'dates' in selected_snippet.metadata and selected_snippet.metadata['dates']:
            dates = selected_snippet.metadata['dates']
            formatted_dates = format_value(dates)
            metadata_rows.append(f"| **Key Dates** | {formatted_dates} |")
        
        if 'attorneys' in selected_snippet.metadata and selected_snippet.metadata['attorneys']:
            attorneys = selected_snippet.metadata['attorneys']
            formatted_attorneys = format_value(attorneys)
            metadata_rows.append(f"| **Legal Team** | {formatted_attorneys} |")
    
    # Display the comprehensive table
    table_content = "| Field | Value |\n|-------|-------|\n" + "\n".join(metadata_rows)
    st.markdown(table_content)
    
    # Download file section
    if selected_snippet.metadata and 'presigned_url' in selected_snippet.metadata:
        presigned_url = selected_snippet.metadata['presigned_url']
        if presigned_url:
            st.markdown("### File Download")
            st.markdown(f"""
            <a href="{presigned_url}" target="_blank" style="text-decoration: none;">
                <button style="
                    padding: 0.5rem 1rem;
                    background-color: #10b981;
                    color: white;
                    border: none;
                    border-radius: 0.4rem;
                    font-weight: 500;
                    cursor: pointer;
                    font-size: 0.9rem;
                    transition: all 0.2s;
                " onmouseover="this.style.backgroundColor='#059669'" onmouseout="this.style.backgroundColor='#10b981'">
                    📥 Download file
                </button>
            </a>
            """, unsafe_allow_html=True)
    
    # Footer - compact
    st.markdown("---")
    st.caption(f"Chunk: {selected_snippet.id} | {selected_snippet.title}")
