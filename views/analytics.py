import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json
import os
import glob
from collections import Counter, defaultdict
from typing import List, Dict, Any

class AnalyticsData:
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
                            parts = line.strip().split(' | ', 2)
                            if len(parts) >= 3:
                                timestamp_str = parts[0]
                                json_data = json.loads(parts[2])
                                json_data['log_timestamp'] = timestamp_str
                                self.events.append(json_data)
                        except (json.JSONDecodeError, IndexError):
                            continue
            except FileNotFoundError:
                # Log error if we can't find critical log files
                try:
                    from utils.usage_logger import log_error
                    log_error("analytics_error", f"Log file not found: {log_file}")
                except Exception:
                    pass
                continue
            except Exception as e:
                # Log other errors during log loading
                try:
                    from utils.usage_logger import log_error
                    log_error("analytics_error", f"Error loading log file {log_file}: {str(e)}")
                except Exception:
                    pass
                continue
    
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
        
        return filtered_events
    
    def get_events_dataframe(self) -> pd.DataFrame:
        """Convert events to pandas DataFrame"""
        if not self.events:
            return pd.DataFrame()
        
        rows = []
        for event in self.events:
            row = {
                'timestamp': event.get('timestamp'),
                'event_type': event.get('event_type'),
                'session_id': event.get('session_id'),
                'user_agent': event.get('user_agent', ''),
            }
            
            # Flatten details
            details = event.get('details', {})
            for key, value in details.items():
                row[f'detail_{key}'] = value
            
            rows.append(row)
        
        df = pd.DataFrame(rows)
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        return df

def show_analytics_page():
    """Display the analytics dashboard"""
    # Log analytics access
    try:
        from utils.usage_logger import log_analytics_access
        log_analytics_access("access")
    except Exception:
        pass
    
    st.markdown("""
    <div style="text-align: center; padding: 2rem 0;">
        <h1>Analytics dashboard</h1>
        <p style="color: #666; font-size: 1.1rem;">
            Key performance metrics and usage insights
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Initialize analytics data
    analytics = AnalyticsData()
    
    if not analytics.events:
        st.warning("📭 No usage data found. Start using the application to see analytics.")
        return
    
    # Sidebar filters
    with st.sidebar:
        st.markdown("### 📈 Analytics filters")
        
        # Date range filter
        date_options = {
            "Last 24 hours": 1,
            "Last 7 days": 7,
            "Last 30 days": 30,
            "Last 90 days": 90,
            "All time": None
        }
        
        selected_period = st.selectbox(
            "Time period:",
            options=list(date_options.keys()),
            index=2  # Default to last 30 days
        )
        
        days_filter = date_options[selected_period]
        
        # Apply filter
        if days_filter:
            filtered_events = analytics.filter_by_days(days_filter)
            analytics.events = filtered_events
            
            # Log filter usage
            try:
                from utils.usage_logger import log_analytics_access
                log_analytics_access("filter_change", time_filter=selected_period)
            except Exception:
                pass
        
        st.markdown(f"**Showing:** {len(analytics.events)} events")
        
        # Export options
        st.markdown("---")
        st.markdown("### 📥 Export data")
        
        df = analytics.get_events_dataframe()
        if not df.empty:
            csv = df.to_csv(index=False)
            st.download_button(
                label="Download analytics data (CSV)",
                data=csv,
                file_name=f"analytics_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
    
    # Main dashboard
    if not analytics.events:
        st.info("No data for the selected time period.")
        return
    
    # Key performance metrics
    st.markdown("## Key performance metrics")
    
    event_types = Counter(event['event_type'] for event in analytics.events)
    unique_sessions = len(set(event['session_id'] for event in analytics.events))
    search_count = event_types.get('search', 0)
    doc_views = event_types.get('document_view', 0)
    
    col1, col2, col3, col4 = st.columns(4)
    
    search_events = [e for e in analytics.events if e['event_type'] == 'search']
    
    with col1:
        st.metric("Active sessions", unique_sessions, help="Unique user sessions in selected period")
    
    with col2:
        search_rate = search_count / unique_sessions if unique_sessions > 0 else 0
        st.metric("Searches per session", f"{search_rate:.1f}", help="Average searches performed per session")
    
    with col3:
        if search_count > 0:
            # Calculate unique search sessions that led to document views
            search_sessions_with_docs = set()
            doc_events = [e for e in analytics.events if e['event_type'] == 'document_view']
            for doc_event in doc_events:
                search_sessions_with_docs.add(doc_event['session_id'])
            
            search_sessions = set(e['session_id'] for e in search_events)
            engagement_rate = len(search_sessions_with_docs) / len(search_sessions) * 100 if search_sessions else 0
            st.metric("Document engagement", f"{engagement_rate:.1f}%", help="% of search sessions that led to document views")
        else:
            st.metric("Document engagement", "0%")
    
    with col4:
        if search_events:
            processing_times = [e['details'].get('processing_time', 0) for e in search_events]
            avg_time = sum(processing_times) / len(processing_times) if processing_times else 0
            est_time_saved = search_count * avg_time  # Estimate if all were uncached
            time_saved_min = est_time_saved / 60
            st.metric("Est. time processed", f"{time_saved_min:.1f}m", help="Total processing time for all searches")
        else:
            st.metric("Est. time processed", "0m")
    
    # Search performance insights
    if search_events:
        st.markdown("## Search performance")
        
        queries = [e['details'].get('query', '') for e in search_events]
        result_counts = [e['details'].get('result_count', 0) for e in search_events]
        processing_times = [e['details'].get('processing_time', 0) for e in search_events]
        successful_searches = len([e for e in search_events if e['details'].get('has_results', False)])
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            success_rate = (successful_searches/len(search_events)*100) if search_events else 0
            st.metric("Search success rate", f"{success_rate:.1f}%", help="Searches that returned results")
        
        with col2:
            avg_results = sum(result_counts) / len(result_counts) if result_counts else 0
            st.metric("Avg results per search", f"{avg_results:.1f}", help="Average number of results returned")
        
        with col3:
            # Calculate response times with and without cache
            cached_searches = [e for e in search_events if e['details'].get('processing_time', 0) < 0.5]  # Assume <0.5s is cached
            non_cached_searches = [e for e in search_events if e['details'].get('processing_time', 0) >= 0.5]
            
            if non_cached_searches:
                non_cached_times = [e['details'].get('processing_time', 0) for e in non_cached_searches]
                avg_non_cached = sum(non_cached_times) / len(non_cached_times)
                cache_rate = len(cached_searches) / len(search_events) * 100
                st.metric("Avg response time (uncached)", f"{avg_non_cached:.2f}s", 
                         help=f"Average response time for non-cached searches. Cache hit rate: {cache_rate:.1f}%")
            else:
                avg_time = sum(processing_times) / len(processing_times) if processing_times else 0
                st.metric("Avg response time", f"{avg_time:.2f}s", help="Average search processing time")
        
        # Most valuable queries
        if queries:
            st.markdown("### Most common search topics")
            query_counter = Counter(q[:60] + '...' if len(q) > 60 else q for q in queries if q)
            if query_counter:
                top_queries = query_counter.most_common(8)
                query_df = pd.DataFrame([
                    {"Query": k, "Count": v, "Impact": f"{v/len(queries)*100:.1f}% of searches"}
                    for k, v in top_queries
                ])
                st.dataframe(query_df, use_container_width=True, hide_index=True)
        
        # Client usage patterns
        client_filters = [e['details'].get('client_filter') for e in search_events if e['details'].get('client_filter') and e['details'].get('client_filter') != 'All']
        if client_filters:
            st.markdown("### Client usage patterns")
            client_counter = Counter(client_filters)
            if len(client_counter) > 1:
                top_clients = client_counter.most_common(10)
                client_df = pd.DataFrame([
                    {"Client": k, "Searches": v, "Usage %": f"{v/sum(client_counter.values())*100:.1f}%"}
                    for k, v in top_clients
                ])
                st.dataframe(client_df, use_container_width=True, hide_index=True)
    
    # Daily activity trends
    df = analytics.get_events_dataframe()
    if not df.empty and 'timestamp' in df.columns and len(df) > 1:
        st.markdown("## Usage trends")
        
        # Focus on search activity over time
        search_df = df[df['event_type'] == 'search'].copy()
        if not search_df.empty:
            search_df['date'] = search_df['timestamp'].dt.date
            daily_searches = search_df.groupby('date').size().reset_index(name='searches')
            
            if len(daily_searches) > 1:
                fig_daily = px.line(
                    daily_searches,
                    x='date',
                    y='searches',
                    title="Daily search activity",
                    markers=True
                )
                fig_daily.update_layout(showlegend=False)
                st.plotly_chart(fig_daily, use_container_width=True)
    
    # System health indicators
    error_events = [e for e in analytics.events if e['event_type'] == 'error']
    if error_events or search_events:
        st.markdown("## System health")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            error_rate = len(error_events) / len(analytics.events) * 100 if analytics.events else 0
            delta_color = "normal" if error_rate < 5 else "inverse"
            st.metric("Error rate", f"{error_rate:.1f}%", delta=None, delta_color=delta_color)
        
        with col2:
            if search_events:
                fast_searches = sum(1 for e in search_events if e['details'].get('processing_time', 0) < 2.0)
                performance_score = (fast_searches / len(search_events) * 100) if search_events else 0
                st.metric("Fast searches (<2s)", f"{performance_score:.1f}%", help="Searches completed in under 2 seconds")
        
        with col3:
            # Show recent activity
            recent_24h_events = analytics.filter_by_days(1)
            st.metric("Activity (24h)", len(recent_24h_events), help="Events in last 24 hours")
    
    # Raw data (show all rows, ordered by timestamp descending)
    st.markdown("## Raw data")
    
    with st.expander("View event data"):
        if not df.empty:
            # Sort by timestamp descending (latest first)
            df_sorted = df.sort_values('timestamp', ascending=False)
            st.dataframe(df_sorted, use_container_width=True, hide_index=True)
            
            # Export options
            col1, col2 = st.columns(2)
            with col1:
                all_csv = df_sorted.to_csv(index=False)
                st.download_button(
                    label="Download all data (CSV)",
                    data=all_csv,
                    file_name=f"all_events_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
            
            with col2:
                search_df = df_sorted[df_sorted['event_type'] == 'search'].copy()
                if not search_df.empty:
                    search_csv = search_df.to_csv(index=False)
                    st.download_button(
                        label="Download search data (CSV)",
                        data=search_csv,
                        file_name=f"search_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv"
                    )
        else:
            st.info("No data to display")
