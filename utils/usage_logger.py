import logging
import os
import json
from datetime import datetime
from typing import Optional, Dict, Any
import streamlit as st
from logging.handlers import RotatingFileHandler

class UsageLogger:
    """Simple usage logger for tracking Legal RAG application usage"""
    
    def __init__(self, log_dir: str = "logs"):
        self.log_dir = log_dir
        self.ensure_log_directory()
        self.logger = self.setup_logger()
    
    def ensure_log_directory(self):
        """Create logs directory if it doesn't exist"""
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
    
    def setup_logger(self) -> logging.Logger:
        """Setup rotating file logger"""
        logger = logging.getLogger('legal_rag_usage')
        logger.setLevel(logging.INFO)
        
        # Avoid duplicate handlers
        if logger.handlers:
            return logger
        
        # Create rotating file handler (5MB max, keep 5 backup files)
        log_file = os.path.join(self.log_dir, 'usage.log')
        handler = RotatingFileHandler(
            log_file, 
            maxBytes=5*1024*1024,  # 5MB
            backupCount=5
        )
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        
        logger.addHandler(handler)
        return logger
    
    def get_session_id(self) -> str:
        """Get or create a session ID"""
        if 'session_id' not in st.session_state:
            st.session_state.session_id = datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:-3]
        return st.session_state.session_id
    
    def log_event(self, event_type: str, details: Dict[str, Any] = None):
        """Log a usage event"""
        try:
            session_id = self.get_session_id()
            log_data = {
                'session_id': session_id,
                'event_type': event_type,
                'timestamp': datetime.now().isoformat(),
                'details': details or {}
            }
            
            # Format as JSON for easier parsing
            log_message = json.dumps(log_data, default=str)
            self.logger.info(log_message)
            
        except Exception as e:
            # Logging should never break the app
            print(f"Logging error: {e}")
    
    def log_search(self, query: str, client_filter: Optional[str] = None, 
                   doc_type_filter: Optional[str] = None, result_count: int = 0, 
                   processing_time: float = 0.0):
        """Log a search operation"""
        self.log_event('search', {
            'query': query[:200],  # Truncate long queries
            'query_length': len(query),
            'client_filter': client_filter,
            'doc_type_filter': doc_type_filter,
            'result_count': result_count,
            'processing_time': processing_time,
            'has_results': result_count > 0
        })
    
    def log_document_view(self, document_id: str, source: str = 'search_results'):
        """Log when a user views a document"""
        self.log_event('document_view', {
            'document_id': document_id,
            'source': source  # 'search_results', 'history', etc.
        })
    
    def log_navigation(self, from_page: str, to_page: str):
        """Log page navigation"""
        self.log_event('navigation', {
            'from_page': from_page,
            'to_page': to_page
        })
    
    def log_session_start(self):
        """Log when a new session starts"""
        self.log_event('session_start', {
            'user_agent': self.get_user_agent(),
            'session_id': self.get_session_id()
        })
    
    def log_error(self, error_type: str, error_message: str, context: Dict[str, Any] = None):
        """Log application errors"""
        self.log_event('error', {
            'error_type': error_type,
            'error_message': error_message[:500],  # Truncate long error messages
            'context': context or {}
        })
    
    def log_predefined_query_usage(self, query_id: str, query_title: str):
        """Log usage of predefined queries"""
        self.log_event('predefined_query', {
            'query_id': query_id,
            'query_title': query_title
        })
    
    def get_user_agent(self) -> str:
        """Get user agent if available"""
        try:
            # This might not always be available in Streamlit
            return str(st.context.headers.get('User-Agent', 'Unknown'))
        except:
            return 'Unknown'

# Global logger instance
_usage_logger = None

def get_usage_logger() -> UsageLogger:
    """Get the global usage logger instance"""
    global _usage_logger
    if _usage_logger is None:
        _usage_logger = UsageLogger()
    return _usage_logger

# Convenience functions for easy import
def log_search(query: str, client_filter: Optional[str] = None, 
               doc_type_filter: Optional[str] = None, result_count: int = 0, 
               processing_time: float = 0.0):
    get_usage_logger().log_search(query, client_filter, doc_type_filter, result_count, processing_time)

def log_document_view(document_id: str, source: str = 'search_results'):
    get_usage_logger().log_document_view(document_id, source)

def log_navigation(from_page: str, to_page: str):
    get_usage_logger().log_navigation(from_page, to_page)

def log_session_start():
    get_usage_logger().log_session_start()

def log_error(error_type: str, error_message: str, context: Dict[str, Any] = None):
    get_usage_logger().log_error(error_type, error_message, context)

def log_predefined_query_usage(query_id: str, query_title: str):
    get_usage_logger().log_predefined_query_usage(query_id, query_title)
