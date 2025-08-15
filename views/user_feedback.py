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

def show_user_feedback_page():
    """Display the user feedback analytics page"""
    # Log feedback analytics access
    try:
        from utils.usage_logger import log_analytics_access
        log_analytics_access("feedback_analytics_access")
    except Exception:
        pass
    
    st.markdown("""
    <div style="text-align: center; padding: 2rem 0;">
        <h1>User feedback</h1>
        <p style="color: #666; font-size: 1.1rem;">
            User satisfaction and feedback insights
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Initialize analytics data
    from views.analytics import AnalyticsData
    analytics = AnalyticsData()
    
    # Filter for feedback events
    feedback_events = [e for e in analytics.events if e['event_type'] == 'feedback']
    
    if not feedback_events:
        st.warning("📭 No user feedback data found yet. Encourage users to provide feedback to see insights here.")
        st.markdown("""
        **How users can provide feedback:**
        - Click on answer details in search results
        - Use the feedback form that appears in answer dialogs
        - Submit ratings and optional comments
        """)
        return
    
    # Sidebar filters
    with st.sidebar:
        st.markdown("### 💬 Feedback filters")
        
        # Date range filter
        date_options = {
            "Last 7 days": 7,
            "Last 30 days": 30,
            "Last 90 days": 90,
            "All time": None
        }
        
        selected_period = st.selectbox(
            "Time period:",
            options=list(date_options.keys()),
            index=1  # Default to last 30 days
        )
        
        days_filter = date_options[selected_period]
        
        # Apply filter
        if days_filter:
            cutoff = datetime.now() - timedelta(days=days_filter)
            feedback_events = [
                e for e in feedback_events
                if datetime.fromisoformat(e['timestamp'].replace('Z', '+00:00')) >= cutoff
            ]
        
        st.markdown(f"**Showing:** {len(feedback_events)} feedback entries")
        
        # Export options
        st.markdown("---")
        st.markdown("### 📥 Export feedback")
        
        if feedback_events:
            feedback_df = create_feedback_dataframe(feedback_events)
            csv = feedback_df.to_csv(index=False)
            st.download_button(
                label="Download feedback data (CSV)",
                data=csv,
                file_name=f"user_feedback_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
    
    # Main feedback analysis
    if not feedback_events:
        st.info("No feedback data for the selected time period.")
        return
    
    # Key feedback metrics
    st.markdown("## Feedback overview")
    
    feedback_types = Counter(e['details'].get('feedback_type', 'Unknown') for e in feedback_events)
    custom_feedback_count = sum(1 for e in feedback_events if e['details'].get('has_custom_feedback', False))
    unique_clients = len(set(e['details'].get('client') for e in feedback_events if e['details'].get('client')))
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total feedback", len(feedback_events), help="Total feedback entries received")
    
    with col2:
        custom_rate = (custom_feedback_count / len(feedback_events) * 100) if feedback_events else 0
        st.metric("Detailed feedback", f"{custom_rate:.1f}%", help="Feedback with custom comments")
    
    with col3:
        st.metric("Clients providing feedback", unique_clients, help="Number of different clients giving feedback")
    
    with col4:
        # Calculate satisfaction rate (positive feedback types)
        positive_feedback = sum(v for k, v in feedback_types.items() 
                               if 'accurate' in k.lower() or 'helpful' in k.lower())
        satisfaction_rate = (positive_feedback / len(feedback_events) * 100) if feedback_events else 0
        st.metric("Satisfaction rate", f"{satisfaction_rate:.1f}%", help="% of positive feedback")
    
    # Feedback type distribution
    st.markdown("## Feedback distribution")
    
    col1, col2 = st.columns([3, 2])
    
    with col1:
        if feedback_types:
            # Simplify feedback type names for display
            simplified_types = {}
            for feedback_type, count in feedback_types.items():
                if 'accurate' in feedback_type.lower():
                    simplified_types['Accurate & Helpful'] = simplified_types.get('Accurate & Helpful', 0) + count
                elif 'partially' in feedback_type.lower():
                    simplified_types['Partially Correct'] = simplified_types.get('Partially Correct', 0) + count
                elif 'incorrect' in feedback_type.lower() or 'misleading' in feedback_type.lower():
                    simplified_types['Incorrect/Misleading'] = simplified_types.get('Incorrect/Misleading', 0) + count
                elif 'lacks' in feedback_type.lower() or 'detail' in feedback_type.lower():
                    simplified_types['Needs More Detail'] = simplified_types.get('Needs More Detail', 0) + count
                else:
                    simplified_types['Other'] = simplified_types.get('Other', 0) + count
            
            fig_feedback = px.pie(
                values=list(simplified_types.values()),
                names=list(simplified_types.keys()),
                title="Feedback type distribution",
                color_discrete_sequence=px.colors.qualitative.Set3
            )
            st.plotly_chart(fig_feedback, use_container_width=True)
    
    with col2:
        feedback_summary_df = pd.DataFrame([
            {"Feedback Type": k, "Count": v, "Percentage": f"{v/len(feedback_events)*100:.1f}%"}
            for k, v in simplified_types.items()
        ])
        st.dataframe(feedback_summary_df, use_container_width=True, hide_index=True)
    
    # Most common feedback topics
    if custom_feedback_count > 0:
        st.markdown("## Common feedback themes")
        
        custom_feedback_list = [
            e['details'].get('custom_feedback', '').strip()
            for e in feedback_events
            if e['details'].get('has_custom_feedback', False) and e['details'].get('custom_feedback', '').strip()
        ]
        
        if custom_feedback_list:
            # Show sample feedback
            st.markdown("### Recent detailed feedback")
            recent_feedback = []
            for event in feedback_events[-10:]:  # Last 10 feedback entries
                details = event['details']
                if details.get('has_custom_feedback', False):
                    recent_feedback.append({
                        "Date": datetime.fromisoformat(event['timestamp'].replace('Z', '+00:00')).strftime('%m/%d %H:%M'),
                        "Type": simplify_feedback_type(details.get('feedback_type', 'Unknown')),
                        "Client": details.get('client', 'Unknown')[:20],
                        "Question": details.get('question', '')[:50] + '...' if len(details.get('question', '')) > 50 else details.get('question', ''),
                        "Comment": details.get('custom_feedback', '')[:100] + '...' if len(details.get('custom_feedback', '')) > 100 else details.get('custom_feedback', '')
                    })
            
            if recent_feedback:
                recent_feedback_df = pd.DataFrame(recent_feedback)
                st.dataframe(recent_feedback_df, use_container_width=True, hide_index=True)
    
    # Feedback over time
    if len(feedback_events) > 1:
        st.markdown("## Feedback trends")
        
        feedback_df = create_feedback_dataframe(feedback_events)
        feedback_df['date'] = pd.to_datetime(feedback_df['timestamp']).dt.date
        
        daily_feedback = feedback_df.groupby(['date', 'feedback_category']).size().reset_index(name='count')
        
        if not daily_feedback.empty:
            fig_trend = px.line(
                daily_feedback,
                x='date',
                y='count',
                color='feedback_category',
                title="Daily feedback trends",
                markers=True
            )
            st.plotly_chart(fig_trend, use_container_width=True)
    
    # Client-specific feedback patterns
    client_feedback = defaultdict(list)
    for event in feedback_events:
        client = event['details'].get('client', 'Unknown')
        if client != 'Unknown':
            client_feedback[client].append(event)
    
    if len(client_feedback) > 1:
        st.markdown("## Client feedback patterns")
        
        client_satisfaction = []
        for client, events in client_feedback.items():
            if len(events) >= 3:  # Only show clients with meaningful feedback
                positive_count = sum(
                    1 for e in events
                    if 'accurate' in e['details'].get('feedback_type', '').lower()
                )
                total_count = len(events)
                satisfaction_pct = (positive_count / total_count * 100) if total_count > 0 else 0
                
                client_satisfaction.append({
                    "Client": client,
                    "Total Feedback": total_count,
                    "Satisfaction": f"{satisfaction_pct:.1f}%",
                    "Detailed Comments": sum(1 for e in events if e['details'].get('has_custom_feedback', False))
                })
        
        if client_satisfaction:
            client_df = pd.DataFrame(client_satisfaction)
            client_df = client_df.sort_values('Total Feedback', ascending=False)
            st.dataframe(client_df, use_container_width=True, hide_index=True)
    
    # System improvement insights
    st.markdown("## Improvement insights")
    
    improvement_issues = []
    negative_feedback = [
        e for e in feedback_events
        if ('incorrect' in e['details'].get('feedback_type', '').lower() or
            'misleading' in e['details'].get('feedback_type', '').lower() or
            'lacks' in e['details'].get('feedback_type', '').lower())
    ]
    
    if negative_feedback:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### Areas needing attention")
            issue_count = len(negative_feedback)
            improvement_rate = ((len(feedback_events) - issue_count) / len(feedback_events) * 100) if feedback_events else 0
            
            st.metric("Issues to address", issue_count)
            st.metric("Overall quality score", f"{improvement_rate:.1f}%")
            
        with col2:
            st.markdown("### Recent issues")
            recent_issues = []
            for event in negative_feedback[-5:]:  # Last 5 issues
                recent_issues.append({
                    "Date": datetime.fromisoformat(event['timestamp'].replace('Z', '+00:00')).strftime('%m/%d'),
                    "Issue": simplify_feedback_type(event['details'].get('feedback_type', 'Unknown')),
                    "Query": event['details'].get('question', '')[:40] + '...' if len(event['details'].get('question', '')) > 40 else event['details'].get('question', '')
                })
            
            if recent_issues:
                issues_df = pd.DataFrame(recent_issues)
                st.dataframe(issues_df, use_container_width=True, hide_index=True)
    else:
        st.success("🎉 Great job! No major issues reported in recent feedback.")
    
    # Raw feedback data
    st.markdown("## Raw feedback data")
    
    with st.expander("View all feedback entries"):
        feedback_df = create_feedback_dataframe(feedback_events)
        
        # Implement chunking for large datasets
        chunk_size = 25
        total_rows = len(feedback_df)
        
        if total_rows > chunk_size:
            # Add pagination
            if 'feedback_chunk_start' not in st.session_state:
                st.session_state.feedback_chunk_start = 0
            
            max_start = max(0, total_rows - chunk_size)
            
            col1, col2, col3 = st.columns([1, 2, 1])
            
            with col1:
                if st.button("⬅️ Previous", key="fb_prev", disabled=st.session_state.feedback_chunk_start <= 0):
                    st.session_state.feedback_chunk_start = max(0, st.session_state.feedback_chunk_start - chunk_size)
                    st.rerun()
            
            with col2:
                current_end = min(st.session_state.feedback_chunk_start + chunk_size, total_rows)
                st.write(f"Showing rows {st.session_state.feedback_chunk_start + 1}-{current_end} of {total_rows}")
            
            with col3:
                if st.button("➡️ Next", key="fb_next", disabled=st.session_state.feedback_chunk_start >= max_start):
                    st.session_state.feedback_chunk_start = min(max_start, st.session_state.feedback_chunk_start + chunk_size)
                    st.rerun()
            
            # Show chunk
            chunk_df = feedback_df.iloc[st.session_state.feedback_chunk_start:st.session_state.feedback_chunk_start + chunk_size]
            st.dataframe(chunk_df, use_container_width=True, hide_index=True)
        else:
            st.dataframe(feedback_df, use_container_width=True, hide_index=True)

def create_feedback_dataframe(feedback_events: List[Dict]) -> pd.DataFrame:
    """Convert feedback events to a pandas DataFrame"""
    rows = []
    for event in feedback_events:
        details = event['details']
        rows.append({
            'timestamp': event['timestamp'],
            'client': details.get('client', 'Unknown'),
            'question': details.get('question', '')[:100] + '...' if len(details.get('question', '')) > 100 else details.get('question', ''),
            'feedback_type': details.get('feedback_type', 'Unknown'),
            'feedback_category': simplify_feedback_type(details.get('feedback_type', 'Unknown')),
            'has_custom_feedback': details.get('has_custom_feedback', False),
            'custom_feedback': details.get('custom_feedback', '')[:200] + '...' if len(details.get('custom_feedback', '')) > 200 else details.get('custom_feedback', ''),
            'answer_preview': details.get('answer', '')[:100] + '...' if len(details.get('answer', '')) > 100 else details.get('answer', '')
        })
    
    df = pd.DataFrame(rows)
    if not df.empty and 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values('timestamp', ascending=False)
    
    return df

def simplify_feedback_type(feedback_type: str) -> str:
    """Simplify feedback type names for better display"""
    feedback_type_lower = feedback_type.lower()
    
    if 'accurate' in feedback_type_lower and 'helpful' in feedback_type_lower:
        return 'Positive'
    elif 'partially' in feedback_type_lower:
        return 'Partial'
    elif 'incorrect' in feedback_type_lower or 'misleading' in feedback_type_lower:
        return 'Incorrect'
    elif 'lacks' in feedback_type_lower or 'detail' in feedback_type_lower:
        return 'Needs Detail'
    else:
        return 'Other'
