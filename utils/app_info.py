import streamlit as st
from datetime import datetime

APP_VERSION = "0.25.08.18"
APP_NAME = "Legal RAG"

CHANGELOG = [
    {
        "version": "0.25.08.18",
        "date": "August 18, 2025",
        "highlights": [
            "🎨 Enhanced dark theme compatibility and UI improvements",
            "🚀 Improved server status handling during embedding model startup",
            "🔧 Fixed dialog popup text visibility issues"
        ],
        "changes": [
            "Fixed logo positioning to prevent overlap with Streamlit menu bar in dark theme",
            "Enhanced answer matrix font colors for better visibility in dark theme mode",
            "Fixed dialog popup text color to use black font for improved readability",
            "Improved server status page handling when embedding model is initializing",
            "Enhanced user experience during server startup with better status feedback",
            "Added proper styling adjustments for dark theme compatibility across all components",
            "Refined UI components to maintain consistency between light and dark theme modes"
        ]
    },
    {
        "version": "0.25.08.15",
        "date": "August 15, 2025",
        "highlights": [
            "📊 Refined analytics dashboard with meaningful performance metrics",
            "💬 Added comprehensive user feedback analytics system",
            "🎨 Added light/dark theme toggle functionality",
            "⚡ Enhanced search performance insights with cache analysis",
            "📈 Improved data visualization and user engagement tracking",
            "🔧 Fixed document engagement calculation and raw data display"
        ],
        "changes": [
            "Created dedicated user feedback analytics page with satisfaction metrics and trend analysis",
            "Added user feedback navigation button in admin panel for comprehensive feedback insights",
            "Fixed document engagement calculation to show meaningful percentage based on unique search sessions",
            "Enhanced analytics metrics to focus on actionable insights (searches per session, engagement rates)",
            "Added cache vs non-cache response time analysis in search performance metrics",
            "Improved raw data table to show all events sorted by timestamp (latest first) without chunking",
            "Added estimated time processed metric showing total search processing time across all queries",
            "Enhanced client usage patterns display with usage percentages and impact analysis",
            "Implemented user feedback logging integration in answer dialogs with detailed context tracking",
            "Added feedback trend analysis with daily feedback patterns and client-specific satisfaction rates",
            "Created feedback categorization system (Positive, Partial, Incorrect, Needs Detail)",
            "Added system improvement insights based on negative feedback patterns",
            "Implemented light/dark theme toggle functionality in sidebar for better user experience",
            "Enhanced theme persistence across user sessions with proper state management",
            "Removed cache information section from cache management page for cleaner interface",
            "Added feedback analytics access logging for admin usage tracking",
            "Improved analytics dashboard performance with optimized data processing",
            "Enhanced search success rate calculations with better result validation",
            "Added activity timeline focused on meaningful search patterns and trends",
            "Implemented system health indicators with error rate monitoring and fast search percentages"
        ]
    },
    {
        "version": "0.25.08.12",
        "date": "August 12, 2025",
        "highlights": [
            "🗄️ Added comprehensive cache management system for admin users",
            "🔧 Fixed embedding API response parsing issues",
            "📋 Enhanced document metadata display with individual field extraction",
            "🎯 Improved query priority handling in search interface",
            "♻️ Code cleanup and redundancy removal for better maintainability",
            "📊 Standardized search results display format across all scenarios"
        ],
        "changes": [
            "Created comprehensive cache management page with statistics, controls, and performance insights",
            "Added cache toggle functionality to enable/disable caching without losing existing cache",
            "Implemented cache clearing options: clear all cache and clear old cache (7+ days)",
            "Added cache performance metrics: total files, size, estimated time saved, efficiency score",
            "Fixed critical embedding API bug - updated response parsing to handle both old (body-wrapped) and new (direct embeddings) formats",
            "Enhanced document metadata display to show individual fields instead of aggregated arrays",
            "Updated dates array extraction to show: Document created on, Document effective date, Document title",
            "Updated attorneys array extraction to show: Contract requester, Reviewing attorney", 
            "Fixed query priority logic - custom queries now properly override predefined queries and 'All questions' selection",
            "Added specific feedback messages when custom queries take priority over other selections",
            "Standardized single client search results to display dataframe format like multi-client searches",
            "Created shared document metadata utility to eliminate code duplication",
            "Refactored metadata extraction logic into reusable functions",
            "Added cache management to admin navigation and main application routing",
            "Enhanced cache file details view with modification times, sizes, and processing information",
            "Implemented cache efficiency scoring and performance insights",
            "Added proper error handling for cache operations with user feedback",
            "Updated index name configuration to 'token-chunking-vectors-poc' for latest vector store"
        ]
    },
    {
        "version": "0.25.08.11",
        "date": "August 11, 2025",
        "highlights": [
            "📊 Added comprehensive analytics dashboard for admin users",
            "🔐 Added login authentication system",
            "🚀 Added automatic server status checking on startup",
            "🛠️ Enhanced error handling for server connectivity",
            "🔧 Fixed multiselect filter clearing functionality",
            "📊 Added app info popover with changelog",
            "⚡ Improved user experience with automatic server health monitoring"
        ],
        "changes": [
            "Created comprehensive analytics dashboard with interactive charts and metrics",
            "Added admin user account with special privileges for analytics access",
            "Enhanced logging system with new event types: authentication, analytics, server_status, filter_usage",
            "Added detailed search logging with all filter parameters (account_type, solution_line, related_product)",
            "Implemented authentication event logging for login/logout with admin status tracking",
            "Added analytics dashboard usage logging with time filters and export tracking",
            "Enhanced server status logging for health checks and cold start attempts",
            "Added filter usage logging and search history replay tracking",
            "Improved error logging in analytics dashboard for better debugging",
            "Implemented data export functionality (CSV downloads) for usage analytics",
            "Added interactive Plotly charts for timeline, heatmaps, and distribution analysis",
            "Created search analytics with query patterns, success rates, and performance metrics",
            "Added document viewing analytics and navigation pattern tracking",
            "Implemented time-based filtering for analytics (24h, 7d, 30d, 90d, all time)",
            "Added error analysis and monitoring with detailed error reporting",
            "Implemented login authentication with credentials stored in secrets.toml",
            "Added user session management with welcome message and logout functionality",
            "Enhanced server status error messages with specific timeout and connection error details",
            "Fixed Account(s) dropdown not clearing properly when Clear button is pressed",
            "Improved cold start error reporting with detailed network diagnostics",
            "Added authentication check before accessing main application features",
            "Server status page now automatically checks embedding server health",
            "Cold start functionality for Ray cluster embedding server",
            "Simplified sidebar navigation by removing redundant buttons",
            "Added version tracking and changelog display",
            "Auto-refresh functionality with 1-minute intervals for server startup"
        ]
    },
    {
        "version": "0.25.08.08", 
        "date": "August 08, 2025",
        "highlights": [
            "🎯 Enhanced search filtering capabilities",
            "📈 Improved search result metrics display",
            "🔍 Added search history functionality"
        ],
        "changes": [
            "Multi-client search support with advanced filtering",
            "Advanced search parameters (relevance threshold, result count)",
            "Search history tracking and replay functionality",
            "Better filter state management across sessions",
            "Improved document type and solution line filtering"
        ]
    },
    {
        "version": "0.25.08.07",
        "date": "August 7, 2025", 
        "highlights": [
            "🎨 Enhanced UI/UX design",
            "📱 Better responsive layout",
            "🔄 Improved session state management"
        ],
        "changes": [
            "Redesigned sidebar with better organization",
            "Added contextual document viewer navigation",
            "Improved filter persistence across page reloads",
            "Better error handling and user feedback",
            "Enhanced search result presentation"
        ]
    }
]

def show_app_info_popover():
    """Display app info and changelog in a popover"""
    if st.button("ℹ️ App info", use_container_width=True, type="secondary"):
        st.session_state.show_app_info = not st.session_state.get('show_app_info', False)
    
    if st.session_state.get('show_app_info', False):
        with st.container():
            st.markdown("---")
            
            # App version header
            st.markdown(f"""
            <div style="text-align: center; padding: 1rem 0; background-color: #f0f2f6; border-radius: 10px; margin-bottom: 1rem;">
                <h2 style="margin: 0; color: #262730;">{APP_NAME}</h2>
                <h3 style="margin: 0.5rem 0; color: #262730;">Version {APP_VERSION} (latest)</h3>
                <p style="color: #666; margin: 0;">Release date: {datetime.now().strftime('%B %d, %Y')}</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Dataset info section
            backend = st.session_state.backend
            clients = backend.get_clients()
            queries = backend.get_predefined_queries()
            
            st.markdown("**📊 Dataset information**")
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Accounts", len(clients) - 1)
            with col2:
                st.metric("Predefined queries", len(queries))
            
            if 'search_results' in st.session_state and st.session_state.search_results:
                results = st.session_state.search_results
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Last results", results.total_documents)
                with col2:
                    st.metric("Search time", f"{results.processing_time:.2f}s")
            
            st.markdown("---")
            
            # Changelog section
            st.markdown("**📝 Changelog**")
            
            for i, version_info in enumerate(CHANGELOG):
                is_latest = i == 0
                expanded = is_latest
                
                with st.expander(f"Version {version_info['version']} {'(latest)' if is_latest else ''} - {version_info['date']}", expanded=expanded):
                    
                    if version_info.get('highlights'):
                        st.markdown("**Highlights**")
                        for highlight in version_info['highlights']:
                            st.markdown(f"• {highlight}")
                        st.markdown("")
                    
                    if version_info.get('changes'):
                        st.markdown("**Notable changes**")
                        for change in version_info['changes']:
                            st.markdown(f"• {change}")
            
            st.markdown("---")
            
            # Close button
            if st.button("✕ Close", key="close_app_info", type="primary", use_container_width=True):
                st.session_state.show_app_info = False
                st.rerun()

def get_app_version():
    """Get current app version"""
    return APP_VERSION

def get_app_name():
    """Get app name"""
    return APP_NAME
