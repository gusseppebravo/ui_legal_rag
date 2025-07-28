"""
FastAPI Client for RAG Backend
Simple HTTP client for connecting to containerized RAG service
"""

import time
import random
import requests
from typing import List, Optional
from datetime import datetime
from .models import DocumentSnippet, SearchResult, FullDocument, PredefinedQuery
from .config import get_endpoint, get_headers, REQUEST_TIMEOUT

class FastAPIRAGClient:
    """
    FastAPI client for RAG backend integration.
    Replace with actual API calls when your FastAPI service is ready.
    """
    
    def __init__(self):
        self.use_mock = True  # Set to False when FastAPI service is available
        if self.use_mock:
            self._init_mock_data()
    
    def _init_mock_data(self):
        """Initialize mock data for development"""
        self.mock_queries = [
            PredefinedQuery(
                id="1",
                title="Are there any limitations on storing client data (including PHI) in the cloud?",
                description="Search for cloud storage restrictions and PHI compliance requirements",
                query_text="Are there any limitations on storing client data (including PHI) in the cloud?",
                category="compliance"
            ),
            PredefinedQuery(
                id="2",
                title="What are the privacy requirements for client data?",
                description="Find privacy policies and data protection requirements",
                query_text="What are the privacy requirements for client data?",
                category="privacy"
            ),
            PredefinedQuery(
                id="3",
                title="What are the data retention requirements?",
                description="Locate data retention policies and timelines",
                query_text="What are the data retention requirements?",                category="retention"
            ),
        ]
        
        self.mock_clients = ["All", "Aetna", "Anthem", "UHC CSP", "BlueCross", "Humana"]
        self.mock_documents = {
            "snippet_1": FullDocument(
                id="doc_aetna_001",
                title="Aetna Business Associate Agreement - Data Processing Addendum",
                content="""
# BUSINESS ASSOCIATE AGREEMENT
## Data Processing and Privacy Requirements

### 1. DEFINITIONS
**"Protected Health Information" (PHI)** means individually identifiable health information that is transmitted or maintained in any form or medium by Business Associate on behalf of Covered Entity.

**"Minimum Necessary"** means the minimum amount of PHI necessary to accomplish the intended purpose of the use, disclosure, or request.

### 2. DATA STORAGE AND CLOUD LIMITATIONS

#### 2.1 Cloud Storage Restrictions
Business Associate may store PHI in cloud environments provided that:
- All data is encrypted using AES-256 encryption both in transit and at rest
- Cloud providers maintain SOC 2 Type II certification
- Data centers are located within the United States
- Multi-factor authentication is required for all administrative access

#### 2.2 Geographic Limitations
PHI shall not be stored, processed, or transmitted outside of the United States without prior written consent from Aetna. This includes:
- Primary data storage locations
- Backup and disaster recovery sites
- Temporary processing locations for analytics

### 3. PRIVACY REQUIREMENTS

#### 3.1 HIPAA Compliance
Business Associate must maintain compliance with:
- HIPAA Privacy Rule (45 CFR Part 164, Subpart E)
- HIPAA Security Rule (45 CFR Part 164, Subpart C)
- HIPAA Breach Notification Rule (45 CFR Part 164, Subpart D)

#### 3.2 Data Minimization
Access to PHI must be limited to the minimum necessary to:
- Perform contracted services
- Comply with legal obligations
- Respond to authorized requests

### 4. SECURITY STANDARDS

#### 4.1 Required Certifications
- SOC 2 Type II (annual)
- ISO 27001 certification
- HITRUST CSF certification (preferred)

#### 4.2 Security Controls
- Network segmentation and firewalls
- Intrusion detection and prevention systems
- Regular vulnerability assessments
- Penetration testing (annual)
- Security awareness training for all personnel

### 5. DATA RETENTION AND DISPOSAL

#### 5.1 Retention Periods
- PHI: 7 years from date of creation or last access
- Audit logs: 7 years minimum
- Backup data: 3 years with secure deletion thereafter

#### 5.2 Secure Disposal
All PHI must be securely destroyed using:
- NIST 800-88 compliant methods for electronic media
- Cross-cut shredding for paper documents
- Certificate of destruction required

### 6. AUDIT AND MONITORING

#### 6.1 Audit Requirements
- Quarterly access reviews
- Annual security assessments
- Real-time monitoring of PHI access
- Incident response procedures

Business Associate shall provide audit logs and compliance reports to Aetna upon request within 30 days.

**Document Version:** 2.1  
**Effective Date:** January 1, 2024  
**Review Date:** January 1, 2025
                """,
                client="Aetna",
                document_type="Business Associate Agreement",
                date_created=datetime(2024, 1, 1),
                sections=[
                    {"title": "1. Definitions", "page": 1},
                    {"title": "2. Data Storage and Cloud Limitations", "page": 2},
                    {"title": "3. Privacy Requirements", "page": 4},
                    {"title": "4. Security Standards", "page": 6},
                    {"title": "5. Data Retention and Disposal", "page": 8},
                    {"title": "6. Audit and Monitoring", "page": 10}
                ],
                metadata={
                    "version": "2.1",
                    "classification": "Confidential",
                    "last_updated": "2024-01-01",
                    "contract_type": "BAA",
                    "jurisdiction": "United States"
                }
            ),
            "snippet_2": FullDocument(
                id="doc_anthem_001", 
                title="Anthem Security and Compliance Framework - Cloud Services Policy",
                content="""
# ANTHEM SECURITY AND COMPLIANCE FRAMEWORK
## Cloud Services and Data Protection Policy

### SECTION I: SCOPE AND APPLICABILITY
This policy applies to all third-party vendors processing Anthem member data, including:
- Claims processing systems
- Provider network platforms
- Analytics and reporting services
- Customer service applications

### SECTION II: CLOUD STORAGE REQUIREMENTS

#### A. Approved Cloud Platforms
Vendors may only utilize cloud services from the following approved providers:
- Amazon Web Services (AWS) - GovCloud regions only
- Microsoft Azure - Government Cloud instances
- Google Cloud Platform - Assured Workloads for Government

#### B. Data Residency Requirements
All Anthem member data must remain within:
- Continental United States
- Dedicated government or healthcare cloud instances
- Facilities with FedRAMP authorization

#### C. Encryption Standards
- Data at rest: AES-256 encryption with FIPS 140-2 Level 3 key management
- Data in transit: TLS 1.3 or higher
- Database encryption: Transparent Data Encryption (TDE) required
- Key rotation: Automated rotation every 90 days

### SECTION III: PRIVACY AND DATA PROTECTION

#### A. Member Data Classification
**Level 1 - Public:** General health information, marketing materials
**Level 2 - Internal:** Aggregated, de-identified data
**Level 3 - Confidential:** PHI, PII, claims data
**Level 4 - Restricted:** Substance abuse, mental health, genetic information

#### B. Access Controls
- Role-based access control (RBAC) implementation
- Privileged access management (PAM) for administrative functions
- Just-in-time access for temporary elevated permissions
- Multi-factor authentication required for all access

#### C. Data Processing Limitations
Member data may only be processed for:
- Contracted business purposes
- Regulatory compliance requirements
- Healthcare operations as defined by HIPAA
- Quality improvement initiatives (with proper safeguards)

### SECTION IV: SECURITY CONTROL REQUIREMENTS

#### A. Mandatory Security Frameworks
Vendors must implement and maintain:
- NIST Cybersecurity Framework (Core functions)
- ISO 27001:2013 Information Security Management
- HITRUST CSF (Healthcare Industry Framework)
- SOC 2 Type II with annual attestation

#### B. Network Security Requirements
- Network segmentation between environments
- Intrusion detection/prevention systems (IDS/IPS)
- Web application firewalls (WAF) for internet-facing applications
- DDoS protection and mitigation
- Network traffic monitoring and analysis

#### C. Endpoint Security
- Endpoint detection and response (EDR) solutions
- Mobile device management (MDM) for BYOD
- Application whitelisting on critical systems
- Regular vulnerability scanning and patching

### SECTION V: MONITORING AND INCIDENT RESPONSE

#### A. Continuous Monitoring
- 24/7 security operations center (SOC) monitoring
- Real-time threat detection and alerting
- User behavior analytics (UBA)
- File integrity monitoring (FIM)

#### B. Incident Response Requirements
- Notification to Anthem within 4 hours of discovery
- Detailed incident reports within 24 hours
- Root cause analysis within 72 hours
- Remediation plan within 5 business days

### SECTION VI: AUDIT AND COMPLIANCE

#### A. Regular Assessments
- Annual third-party security assessments
- Quarterly vulnerability assessments
- Monthly access reviews and certifications
- Annual business continuity testing

#### B. Documentation Requirements
Vendors must maintain and provide upon request:
- Current security policies and procedures
- Employee training records
- Incident response documentation
- Change management records
- Vendor risk assessments

**Policy Number:** ANT-SEC-001  
**Version:** 3.2  
**Effective Date:** March 15, 2024  
**Next Review:** March 15, 2025  
**Approval Authority:** Chief Information Security Officer
                """,
                client="Anthem",
                document_type="Security Policy",
                date_created=datetime(2024, 3, 15),
                sections=[
                    {"title": "Section I: Scope and Applicability", "page": 1},
                    {"title": "Section II: Cloud Storage Requirements", "page": 2},
                    {"title": "Section III: Privacy and Data Protection", "page": 5},
                    {"title": "Section IV: Security Control Requirements", "page": 8},
                    {"title": "Section V: Monitoring and Incident Response", "page": 12},
                    {"title": "Section VI: Audit and Compliance", "page": 15}
                ],
                metadata={
                    "version": "3.2",
                    "classification": "Confidential - Internal Use Only",
                    "last_updated": "2024-03-15",
                    "policy_type": "Security Framework",
                    "compliance_frameworks": ["HIPAA", "SOC 2", "HITRUST", "NIST CSF"]
                }
            )
        }
    
    def get_predefined_queries(self) -> List[PredefinedQuery]:
        """Get predefined queries from FastAPI service"""
        if self.use_mock:
            return self.mock_queries
        
        try:
            response = requests.get(
                get_endpoint("queries"),
                headers=get_headers(),
                timeout=REQUEST_TIMEOUT
            )
            response.raise_for_status()
            data = response.json()
            return [PredefinedQuery(**item) for item in data]
        except requests.RequestException:
            return []
    
    def get_clients(self) -> List[str]:
        """Get available clients from FastAPI service"""
        if self.use_mock:
            return self.mock_clients
        
        try:
            response = requests.get(
                get_endpoint("clients"),
                headers=get_headers(),
                timeout=REQUEST_TIMEOUT
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException:
            return ["All"]
    
    def search_documents(self, query: str, client_filter: Optional[str] = None) -> SearchResult:
        """Search documents using FastAPI service"""
        if self.use_mock:
            return self._mock_search(query, client_filter)
        
        try:
            payload = {"query": query}
            if client_filter and client_filter != "All":
                payload["client_filter"] = client_filter
            
            response = requests.post(
                get_endpoint("search"),
                json=payload,
                headers=get_headers(),
                timeout=REQUEST_TIMEOUT
            )
            response.raise_for_status()
            data = response.json()
            
            return SearchResult(
                query=query,
                snippets=[DocumentSnippet(**snippet) for snippet in data.get("snippets", [])],
                total_documents=data.get("total_documents", 0),
                processing_time=data.get("processing_time", 0.0),
                summary=data.get("summary", "")
            )
        except requests.RequestException as e:
            return SearchResult(
                query=query,
                snippets=[],
                total_documents=0,                processing_time=0.0,
                summary=f"Error: {str(e)}"
            )
    
    def get_full_document(self, document_id: Optional[str]) -> Optional[FullDocument]:
        """Get full document from FastAPI service"""
        if self.use_mock:
            if document_id in self.mock_documents:
                return self.mock_documents[document_id]
            # Default to first document if exact ID not found
            return list(self.mock_documents.values())[0] if self.mock_documents else None
        
        if not document_id:
            return None
        
        try:
            response = requests.get(
                get_endpoint(f"documents/{document_id}"),
                headers=get_headers(),
                timeout=REQUEST_TIMEOUT
            )
            response.raise_for_status()
            data = response.json()
            return FullDocument(**data)
        except requests.RequestException:            return None
    
    def _mock_search(self, query: str, client_filter: Optional[str] = None) -> SearchResult:
        """Mock search for development"""
        time.sleep(random.uniform(0.3, 0.8))
        
        mock_snippets = [
            {
                "title": "Business Associate Agreement - Cloud Storage Limitations",
                "content": "Business Associate may store PHI in cloud environments provided that: All data is encrypted using AES-256 encryption both in transit and at rest, Cloud providers maintain SOC 2 Type II certification, Data centers are located within the United States, Multi-factor authentication is required for all administrative access. PHI shall not be stored, processed, or transmitted outside of the United States without prior written consent from Aetna.",
                "source": "Aetna",
                "score": 0.95
            },
            {
                "title": "Anthem Security Framework - Data Residency Requirements",
                "content": "All Anthem member data must remain within: Continental United States, Dedicated government or healthcare cloud instances, Facilities with FedRAMP authorization. Vendors may only utilize cloud services from approved providers: Amazon Web Services (AWS) - GovCloud regions only, Microsoft Azure - Government Cloud instances, Google Cloud Platform - Assured Workloads for Government.",
                "source": "Anthem", 
                "score": 0.91
            },
            {
                "title": "HIPAA Privacy Rule - Data Minimization Requirements",
                "content": "Access to PHI must be limited to the minimum necessary to: Perform contracted services, Comply with legal obligations, Respond to authorized requests. Business Associate must maintain compliance with HIPAA Privacy Rule (45 CFR Part 164, Subpart E), HIPAA Security Rule (45 CFR Part 164, Subpart C), and HIPAA Breach Notification Rule (45 CFR Part 164, Subpart D).",
                "source": "Aetna",
                "score": 0.89
            },
            {
                "title": "Security Control Requirements - Encryption Standards",
                "content": "Data at rest: AES-256 encryption with FIPS 140-2 Level 3 key management, Data in transit: TLS 1.3 or higher, Database encryption: Transparent Data Encryption (TDE) required, Key rotation: Automated rotation every 90 days. All encryption must comply with healthcare industry standards and government requirements.",
                "source": "Anthem",
                "score": 0.87
            },
            {
                "title": "Data Retention and Disposal Requirements",
                "content": "PHI: 7 years from date of creation or last access, Audit logs: 7 years minimum, Backup data: 3 years with secure deletion thereafter. All PHI must be securely destroyed using NIST 800-88 compliant methods for electronic media, Cross-cut shredding for paper documents, Certificate of destruction required.",
                "source": "Aetna",
                "score": 0.85
            },
            {
                "title": "Audit and Monitoring Requirements",
                "content": "Quarterly access reviews, Annual security assessments, Real-time monitoring of PHI access, Incident response procedures. Business Associate shall provide audit logs and compliance reports to Aetna upon request within 30 days. 24/7 security operations center (SOC) monitoring required with real-time threat detection and alerting.",
                "source": "Anthem",
                "score": 0.83
            }
        ]
        
        snippets = []
        for i, snippet_data in enumerate(mock_snippets):
            if client_filter and client_filter != "All" and snippet_data["source"] != client_filter:
                continue
                
            snippets.append(DocumentSnippet(
                id=f"snippet_{i+1}",
                title=snippet_data["title"],
                content=snippet_data["content"],
                source=snippet_data["source"],
                relevance_score=snippet_data["score"],
                page_number=random.randint(8, 20),
                section=f"Section {random.randint(3, 8)}"
            ))
        
        return SearchResult(
            query=query,
            snippets=snippets,
            total_documents=len(snippets),
            processing_time=random.uniform(0.3, 0.8),
            summary=f"Found {len(snippets)} relevant sections"
        )
