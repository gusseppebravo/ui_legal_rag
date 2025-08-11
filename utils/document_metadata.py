from typing import List, Any
from backend.models import DocumentSnippet

def format_value(value: Any) -> str:
    """Format metadata values for display"""
    if isinstance(value, list):
        return ", ".join(str(v) for v in value if v) if value else "N/A"
    return str(value) if value else "N/A"

def extract_contract_number(snippet: DocumentSnippet) -> str:
    """Extract contract number from s3_path"""
    if not snippet.metadata or 's3_path' not in snippet.metadata:
        return "N/A"
    
    s3_path = snippet.metadata['s3_path']
    if '/contract-docs/' not in s3_path:
        return "N/A"
    
    path_parts = s3_path.split('/contract-docs/')
    if len(path_parts) > 1:
        remaining_path = path_parts[1]
        contract_parts = remaining_path.split('/')
        if contract_parts:
            return contract_parts[0]
    
    return "N/A"

def extract_client_name(snippet: DocumentSnippet) -> str:
    """Extract client name from metadata"""
    if not snippet.metadata:
        return "N/A"
    
    account_details = snippet.metadata.get("account_details", [])
    if isinstance(account_details, list) and len(account_details) > 0:
        return account_details[0] if account_details[0] else "N/A"
    
    # Fallback to old structure if needed
    client_account = snippet.metadata.get("client_account", "N/A")
    if isinstance(client_account, list):
        return client_account[0] if client_account else "N/A"
    else:
        return client_account if client_account != "N/A" else "N/A"

def build_metadata_table(snippet: DocumentSnippet, include_basic_fields: bool = True) -> List[str]:
    """Build metadata table rows for a document snippet"""
    metadata_rows = []
    
    if include_basic_fields:
        client_name = extract_client_name(snippet)
        contract_number = extract_contract_number(snippet)
        
        metadata_rows.append(f"| **Client** | {client_name} |")
        metadata_rows.append(f"| **Contract** | {contract_number} |")
        metadata_rows.append(f"| **Source** | {snippet.source} |")
        metadata_rows.append(f"| **Document type** | {snippet.section or 'N/A'} |")
        metadata_rows.append(f"| **Relevance** | {snippet.relevance_score:.3f} |")
        metadata_rows.append(f"| **Distance** | {snippet.distance:.3f} |")
    
    if not snippet.metadata:
        return metadata_rows
    
    # Key fields from metadata
    key_fields = {
        'contract_title': 'Contract title',
        'solution_line': 'Solution line', 
        'status_reason': 'Status',
        'parent_contract': 'Parent contract'
    }
    
    for field, display_name in key_fields.items():
        if field in snippet.metadata and snippet.metadata[field]:
            value = format_value(snippet.metadata[field])
            metadata_rows.append(f"| **{display_name}** | {value} |")
    
    # Extract individual date fields from dates array
    # dates = [created_on, document_effective_date, document_title]
    if 'dates' in snippet.metadata and snippet.metadata['dates']:
        dates = snippet.metadata['dates']
        if isinstance(dates, list):
            if len(dates) > 0 and dates[0]:
                metadata_rows.append(f"| **Document created on** | {dates[0]} |")
            if len(dates) > 1 and dates[1]:
                metadata_rows.append(f"| **Document effective date** | {dates[1]} |")
            if len(dates) > 2 and dates[2]:
                metadata_rows.append(f"| **Document title** | {dates[2]} |")
    
    # Extract individual attorney fields from attorneys array
    # attorneys = [contract_requester, reviewing_attorney]
    if 'attorneys' in snippet.metadata and snippet.metadata['attorneys']:
        attorneys = snippet.metadata['attorneys']
        if isinstance(attorneys, list):
            if len(attorneys) > 0 and attorneys[0]:
                metadata_rows.append(f"| **Contract requester** | {attorneys[0]} |")
            if len(attorneys) > 1 and attorneys[1]:
                metadata_rows.append(f"| **Reviewing attorney** | {attorneys[1]} |")
    
    return metadata_rows

def format_metadata_table(metadata_rows: List[str]) -> str:
    """Format metadata rows into a markdown table"""
    return "| Field | Value |\n|-------|-------|\n" + "\n".join(metadata_rows)
