#!/usr/bin/env python3
"""
Usage Log Analyzer for Legal RAG Application

Simple utility to analyze usage logs and generate basic statistics.
Usage: python log_analyzer.py [--days N] [--export csv]
"""

import json
import os
import argparse
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from typing import List, Dict, Any
import glob

class LogAnalyzer:
    def __init__(self, log_dir: str = "logs"):
        self.log_dir = log_dir
        self.events = []
        self.load_logs()
    
    def load_logs(self):
        """Load all log files"""
        log_files = glob.glob(os.path.join(self.log_dir, "usage.log*"))
        
        for log_file in sorted(log_files):
            try:
                with open(log_file, 'r') as f:
                    for line in f:
                        try:
                            # Parse log line: timestamp | level | json_data
                            parts = line.strip().split(' | ', 2)
                            if len(parts) >= 3:
                                timestamp_str = parts[0]
                                json_data = json.loads(parts[2])
                                json_data['log_timestamp'] = timestamp_str
                                self.events.append(json_data)
                        except (json.JSONDecodeError, IndexError):
                            continue
            except FileNotFoundError:
                print(f"Log file {log_file} not found")
    
    def filter_by_days(self, days: int):
        """Filter events to last N days"""
        cutoff = datetime.now() - timedelta(days=days)
        filtered_events = []
        
        for event in self.events:
            try:
                event_time = datetime.fromisoformat(event['timestamp'].replace('Z', '+00:00'))
                if event_time >= cutoff:
                    filtered_events.append(event)
            except (ValueError, KeyError):
                continue
        
        self.events = filtered_events
    
    def get_summary_stats(self) -> Dict[str, Any]:
        """Get basic summary statistics"""
        if not self.events:
            return {"error": "No events found"}
        
        event_types = Counter(event['event_type'] for event in self.events)
        unique_sessions = len(set(event['session_id'] for event in self.events))
        
        # Date range
        dates = []
        for event in self.events:
            try:
                dates.append(datetime.fromisoformat(event['timestamp'].replace('Z', '+00:00')))
            except:
                continue
        
        date_range = {}
        if dates:
            date_range = {
                'first_event': min(dates).strftime('%Y-%m-%d %H:%M:%S'),
                'last_event': max(dates).strftime('%Y-%m-%d %H:%M:%S'),
                'total_days': (max(dates) - min(dates)).days + 1
            }
        
        return {
            'total_events': len(self.events),
            'unique_sessions': unique_sessions,
            'event_types': dict(event_types),
            'date_range': date_range
        }
    
    def get_search_analytics(self) -> Dict[str, Any]:
        """Analyze search patterns"""
        search_events = [e for e in self.events if e['event_type'] == 'search']
        
        if not search_events:
            return {"message": "No search events found"}
        
        # Query analysis
        queries = [e['details'].get('query', '') for e in search_events]
        query_lengths = [e['details'].get('query_length', 0) for e in search_events]
        
        # Filter usage
        client_filters = [e['details'].get('client_filter') for e in search_events if e['details'].get('client_filter')]
        doc_type_filters = [e['details'].get('doc_type_filter') for e in search_events if e['details'].get('doc_type_filter')]
        
        # Results analysis
        result_counts = [e['details'].get('result_count', 0) for e in search_events]
        processing_times = [e['details'].get('processing_time', 0) for e in search_events]
        successful_searches = len([e for e in search_events if e['details'].get('has_results', False)])
        
        # Most common queries (first 50 chars)
        query_preview = Counter(q[:50] + '...' if len(q) > 50 else q for q in queries if q)
        
        return {
            'total_searches': len(search_events),
            'successful_searches': successful_searches,
            'success_rate': f"{(successful_searches/len(search_events)*100):.1f}%" if search_events else "0%",
            'avg_query_length': f"{sum(query_lengths)/len(query_lengths):.1f}" if query_lengths else 0,
            'avg_results': f"{sum(result_counts)/len(result_counts):.1f}" if result_counts else 0,
            'avg_processing_time': f"{sum(processing_times)/len(processing_times):.2f}s" if processing_times else "0s",
            'client_filter_usage': dict(Counter(client_filters)),
            'doc_type_filter_usage': dict(Counter(doc_type_filters)),
            'most_common_queries': dict(query_preview.most_common(10))
        }
    
    def get_navigation_patterns(self) -> Dict[str, Any]:
        """Analyze user navigation patterns"""
        nav_events = [e for e in self.events if e['event_type'] == 'navigation']
        
        if not nav_events:
            return {"message": "No navigation events found"}
        
        transitions = [(e['details'].get('from_page'), e['details'].get('to_page')) for e in nav_events]
        transition_counts = Counter(f"{from_p} → {to_p}" for from_p, to_p in transitions)
        
        return {
            'total_navigation_events': len(nav_events),
            'common_transitions': dict(transition_counts.most_common(10))
        }
    
    def get_document_view_stats(self) -> Dict[str, Any]:
        """Analyze document viewing patterns"""
        doc_events = [e for e in self.events if e['event_type'] == 'document_view']
        
        if not doc_events:
            return {"message": "No document view events found"}
        
        sources = Counter(e['details'].get('source', 'unknown') for e in doc_events)
        documents = Counter(e['details'].get('document_id', 'unknown') for e in doc_events)
        
        return {
            'total_document_views': len(doc_events),
            'view_sources': dict(sources),
            'most_viewed_documents': dict(documents.most_common(10))
        }
    
    def get_error_analysis(self) -> Dict[str, Any]:
        """Analyze errors and issues"""
        error_events = [e for e in self.events if e['event_type'] == 'error']
        
        if not error_events:
            return {"message": "No errors found (good!)"}
        
        error_types = Counter(e['details'].get('error_type', 'unknown') for e in error_events)
        
        return {
            'total_errors': len(error_events),
            'error_types': dict(error_types),
            'recent_errors': [
                {
                    'timestamp': e['timestamp'],
                    'type': e['details'].get('error_type'),
                    'message': e['details'].get('error_message', '')[:100]
                }
                for e in error_events[-5:]  # Last 5 errors
            ]
        }
    
    def print_report(self):
        """Print a comprehensive usage report"""
        print("=" * 60)
        print("📊 LEGAL RAG USAGE ANALYTICS REPORT")
        print("=" * 60)
        
        # Summary
        summary = self.get_summary_stats()
        print(f"\n📈 SUMMARY STATISTICS")
        print(f"Total Events: {summary.get('total_events', 0)}")
        print(f"Unique Sessions: {summary.get('unique_sessions', 0)}")
        print(f"Event Types: {summary.get('event_types', {})}")
        if 'date_range' in summary:
            dr = summary['date_range']
            print(f"Date Range: {dr.get('first_event', 'N/A')} to {dr.get('last_event', 'N/A')}")
            print(f"Total Days: {dr.get('total_days', 0)}")
        
        # Search Analytics
        search_stats = self.get_search_analytics()
        print(f"\n🔍 SEARCH ANALYTICS")
        for key, value in search_stats.items():
            if key == 'most_common_queries':
                print(f"Most Common Queries:")
                for query, count in value.items():
                    print(f"  • {query} ({count}x)")
            elif key in ['client_filter_usage', 'doc_type_filter_usage']:
                if value:
                    print(f"{key.replace('_', ' ').title()}: {value}")
            else:
                print(f"{key.replace('_', ' ').title()}: {value}")
        
        # Navigation
        nav_stats = self.get_navigation_patterns()
        print(f"\n🧭 NAVIGATION PATTERNS")
        for key, value in nav_stats.items():
            if key == 'common_transitions':
                print("Common Page Transitions:")
                for transition, count in value.items():
                    print(f"  • {transition} ({count}x)")
            else:
                print(f"{key.replace('_', ' ').title()}: {value}")
        
        # Document Views
        doc_stats = self.get_document_view_stats()
        print(f"\n📄 DOCUMENT VIEW ANALYTICS")
        for key, value in doc_stats.items():
            if isinstance(value, dict) and value:
                print(f"{key.replace('_', ' ').title()}:")
                for item, count in list(value.items())[:5]:  # Top 5
                    print(f"  • {item}: {count}")
            else:
                print(f"{key.replace('_', ' ').title()}: {value}")
        
        # Errors
        error_stats = self.get_error_analysis()
        print(f"\n⚠️ ERROR ANALYSIS")
        for key, value in error_stats.items():
            if key == 'recent_errors':
                if value:
                    print("Recent Errors:")
                    for error in value:
                        print(f"  • [{error['timestamp']}] {error['type']}: {error['message']}")
            else:
                print(f"{key.replace('_', ' ').title()}: {value}")
        
        print("\n" + "=" * 60)

def main():
    parser = argparse.ArgumentParser(description='Analyze Legal RAG usage logs')
    parser.add_argument('--days', type=int, help='Analyze only last N days')
    parser.add_argument('--log-dir', default='logs', help='Log directory path')
    
    args = parser.parse_args()
    
    analyzer = LogAnalyzer(args.log_dir)
    
    if args.days:
        analyzer.filter_by_days(args.days)
        print(f"Analyzing last {args.days} days of usage...")
    
    analyzer.print_report()

if __name__ == "__main__":
    main()
