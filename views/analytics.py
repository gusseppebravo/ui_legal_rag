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
        <h1> Analytics dashboard</h1>
        <p style="color: #666; font-size: 1.1rem;">
            Comprehensive usage analytics and insights
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
                label="Download full data (CSV)",
                data=csv,
                file_name=f"analytics_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
            
            # Log export action when button is clicked
            if st.session_state.get('download_full_data_clicked', False):
                try:
                    from utils.usage_logger import log_analytics_access
                    log_analytics_access("export", export_type="full_data_csv")
                    st.session_state.download_full_data_clicked = False
                except Exception:
                    pass
    
    # Main dashboard
    if not analytics.events:
        st.info("No data for the selected time period.")
        return
    
    # Summary metrics
    st.markdown("## Key metrics")
    
    event_types = Counter(event['event_type'] for event in analytics.events)
    unique_sessions = len(set(event['session_id'] for event in analytics.events))
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total events", len(analytics.events))
    
    with col2:
        st.metric("Unique sessions", unique_sessions)
    
    with col3:
        search_count = event_types.get('search', 0)
        st.metric("Total searches", search_count)
    
    with col4:
        doc_views = event_types.get('document_view', 0)
        st.metric("Document views", doc_views)
    
    # Event types breakdown
    st.markdown("## Event breakdown")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Event types pie chart
        if event_types:
            fig_pie = px.pie(
                values=list(event_types.values()),
                names=list(event_types.keys()),
                title="Event types distribution"
            )
            st.plotly_chart(fig_pie, use_container_width=True)
    
    with col2:
        # Event types table
        event_df = pd.DataFrame([
            {"Event Type": k, "Count": v, "Percentage": f"{v/len(analytics.events)*100:.1f}%"}
            for k, v in event_types.most_common()
        ])
        st.dataframe(event_df, use_container_width=True)
    
    # Timeline analysis
    st.markdown("## Activity timeline")
    
    df = analytics.get_events_dataframe()
    if not df.empty and 'timestamp' in df.columns:
        # Daily activity
        df['date'] = df['timestamp'].dt.date
        daily_activity = df.groupby(['date', 'event_type']).size().reset_index(name='count')
        
        fig_timeline = px.line(
            daily_activity,
            x='date',
            y='count',
            color='event_type',
            title="Daily activity by event type",
            markers=True
        )
        st.plotly_chart(fig_timeline, use_container_width=True)
        
        # Hourly heatmap
        df['hour'] = df['timestamp'].dt.hour
        df['day_of_week'] = df['timestamp'].dt.day_name()
        
        hourly_activity = df.groupby(['day_of_week', 'hour']).size().reset_index(name='count')
        hourly_pivot = hourly_activity.pivot(index='day_of_week', columns='hour', values='count').fillna(0)
        
        # Reorder days of week
        day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        hourly_pivot = hourly_pivot.reindex(day_order)
        
        fig_heatmap = px.imshow(
            hourly_pivot.values,
            x=hourly_pivot.columns,
            y=hourly_pivot.index,
            title="Activity heatmap (by hour and day)",
            color_continuous_scale="Blues",
            aspect="auto"
        )
        st.plotly_chart(fig_heatmap, use_container_width=True)
    
    # Search analytics
    search_events = [e for e in analytics.events if e['event_type'] == 'search']
    
    if search_events:
        st.markdown("## Search analytics")
        
        # Search metrics
        queries = [e['details'].get('query', '') for e in search_events]
        result_counts = [e['details'].get('result_count', 0) for e in search_events]
        processing_times = [e['details'].get('processing_time', 0) for e in search_events]
        successful_searches = len([e for e in search_events if e['details'].get('has_results', False)])
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Success rate", f"{(successful_searches/len(search_events)*100):.1f}%")
        
        with col2:
            avg_results = sum(result_counts) / len(result_counts) if result_counts else 0
            st.metric("Avg results", f"{avg_results:.1f}")
        
        with col3:
            avg_time = sum(processing_times) / len(processing_times) if processing_times else 0
            st.metric("Avg search time", f"{avg_time:.2f}s")
        
        with col4:
            avg_query_length = sum(len(q) for q in queries) / len(queries) if queries else 0
            st.metric("Avg query length", f"{avg_query_length:.0f} chars")
        
        # Search queries analysis
        col1, col2 = st.columns(2)
        
        with col1:
            # Most common queries
            query_counter = Counter(q[:50] + '...' if len(q) > 50 else q for q in queries if q)
            if query_counter:
                query_df = pd.DataFrame([
                    {"Query": k, "Count": v}
                    for k, v in query_counter.most_common(10)
                ])
                st.markdown("**Most common queries**")
                st.dataframe(query_df, use_container_width=True)
        
        with col2:
            # Filter usage
            client_filters = [e['details'].get('client_filter') for e in search_events if e['details'].get('client_filter')]
            if client_filters:
                client_counter = Counter(client_filters)
                client_df = pd.DataFrame([
                    {"Client Filter": k, "Count": v}
                    for k, v in client_counter.most_common(10)
                ])
                st.markdown("**Client filter usage**")
                st.dataframe(client_df, use_container_width=True)
        
        # Search results distribution
        if result_counts:
            fig_results = px.histogram(
                x=result_counts,
                nbins=20,
                title="Search results distribution",
                labels={'x': 'Number of results', 'y': 'Frequency'}
            )
            st.plotly_chart(fig_results, use_container_width=True)
        
        # Processing time analysis
        if processing_times:
            fig_time = px.box(
                y=processing_times,
                title="Search processing time distribution",
                labels={'y': 'Processing time (seconds)'}
            )
            st.plotly_chart(fig_time, use_container_width=True)
    
    # Document viewing analytics
    doc_events = [e for e in analytics.events if e['event_type'] == 'document_view']
    
    if doc_events:
        st.markdown("## Document analytics")
        
        sources = Counter(e['details'].get('source', 'unknown') for e in doc_events)
        documents = Counter(e['details'].get('document_id', 'unknown') for e in doc_events)
        
        col1, col2 = st.columns(2)
        
        with col1:
            if sources:
                source_df = pd.DataFrame([
                    {"View Source": k, "Count": v}
                    for k, v in sources.most_common()
                ])
                st.markdown("**Document view sources**")
                st.dataframe(source_df, use_container_width=True)
        
        with col2:
            if documents:
                doc_df = pd.DataFrame([
                    {"Document ID": k, "Views": v}
                    for k, v in documents.most_common(10)
                ])
                st.markdown("**Most viewed documents**")
                st.dataframe(doc_df, use_container_width=True)
    
    # Navigation patterns
    nav_events = [e for e in analytics.events if e['event_type'] == 'navigation']
    
    if nav_events:
        st.markdown("## Navigation patterns")
        
        transitions = [(e['details'].get('from_page'), e['details'].get('to_page')) for e in nav_events]
        transition_counts = Counter(f"{from_p} → {to_p}" for from_p, to_p in transitions)
        
        if transition_counts:
            nav_df = pd.DataFrame([
                {"Navigation Path": k, "Count": v}
                for k, v in transition_counts.most_common(10)
            ])
            st.dataframe(nav_df, use_container_width=True)
    
    # Error analysis
    error_events = [e for e in analytics.events if e['event_type'] == 'error']
    
    if error_events:
        st.markdown("## ⚠️ Error analysis")
        
        error_types = Counter(e['details'].get('error_type', 'unknown') for e in error_events)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Total errors", len(error_events))
            error_rate = len(error_events) / len(analytics.events) * 100
            st.metric("Error rate", f"{error_rate:.2f}%")
        
        with col2:
            if error_types:
                error_df = pd.DataFrame([
                    {"Error Type": k, "Count": v}
                    for k, v in error_types.most_common()
                ])
                st.dataframe(error_df, use_container_width=True)
        
        # Recent errors
        st.markdown("**Recent errors**")
        recent_errors = []
        for error in error_events[-10:]:  # Last 10 errors
            recent_errors.append({
                "Timestamp": error['timestamp'],
                "Type": error['details'].get('error_type', 'unknown'),
                "Message": error['details'].get('error_message', '')[:100]
            })
        
        if recent_errors:
            error_recent_df = pd.DataFrame(recent_errors)
            st.dataframe(error_recent_df, use_container_width=True)
    
    # Raw data export
    st.markdown("## Raw data")
    
    with st.expander("View raw event data"):
        if not df.empty:
            st.dataframe(df, use_container_width=True)
            
            # Additional export for searches only
            search_df = df[df['event_type'] == 'search'].copy()
            if not search_df.empty:
                search_csv = search_df.to_csv(index=False)
                st.download_button(
                    label="Download search data only (CSV)",
                    data=search_csv,
                    file_name=f"search_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
                
                # Log search data export
                if st.session_state.get('download_search_data_clicked', False):
                    try:
                        from utils.usage_logger import log_analytics_access
                        log_analytics_access("export", export_type="search_data_csv")
                        st.session_state.download_search_data_clicked = False
                    except Exception:
                        pass
        else:
            st.info("No data to display")
