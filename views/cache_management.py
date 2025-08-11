import streamlit as st
import os
import pickle
import glob
from datetime import datetime, timedelta
import time
from typing import Dict, Any, List
import hashlib

class CacheManager:
    def __init__(self, cache_dir: str = "cache"):
        self.cache_dir = cache_dir
        
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics"""
        cache_files = glob.glob(os.path.join(self.cache_dir, "*.pkl"))
        
        if not cache_files:
            return {
                "total_files": 0,
                "total_size_bytes": 0,
                "total_size_mb": 0,
                "oldest_file": None,
                "newest_file": None,
                "avg_file_size_kb": 0,
                "estimated_time_saved": 0
            }
        
        total_size = 0
        file_times = []
        estimated_time_saved = 0
        
        for cache_file in cache_files:
            try:
                # Get file size
                file_size = os.path.getsize(cache_file)
                total_size += file_size
                
                # Get file modification time
                mtime = os.path.getmtime(cache_file)
                file_times.append(mtime)
                
                # Estimate time saved (assume each cached query saves ~5-10 seconds)
                # We'll use a conservative estimate of 6 seconds per cached query
                estimated_time_saved += 6
                
            except (OSError, IOError):
                continue
        
        return {
            "total_files": len(cache_files),
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "oldest_file": datetime.fromtimestamp(min(file_times)) if file_times else None,
            "newest_file": datetime.fromtimestamp(max(file_times)) if file_times else None,
            "avg_file_size_kb": round(total_size / len(cache_files) / 1024, 2) if cache_files else 0,
            "estimated_time_saved": estimated_time_saved
        }
    
    def get_cache_files_info(self) -> List[Dict[str, Any]]:
        """Get detailed information about each cache file"""
        cache_files = glob.glob(os.path.join(self.cache_dir, "*.pkl"))
        files_info = []
        
        for cache_file in cache_files:
            try:
                filename = os.path.basename(cache_file)
                file_size = os.path.getsize(cache_file)
                mtime = os.path.getmtime(cache_file)
                
                # Try to load cache content to get query info
                query_info = "Unknown"
                processing_time = "Unknown"
                try:
                    with open(cache_file, 'rb') as f:
                        cached_data = pickle.load(f)
                        if isinstance(cached_data, tuple) and len(cached_data) >= 3:
                            # If it's a tuple like (answer, refs, latency, chunks)
                            if len(cached_data) > 2 and isinstance(cached_data[2], (int, float)):
                                processing_time = f"{cached_data[2]}ms"
                except Exception:
                    pass
                
                files_info.append({
                    "filename": filename,
                    "cache_key": filename.replace(".pkl", ""),
                    "size_bytes": file_size,
                    "size_kb": round(file_size / 1024, 2),
                    "modified_time": datetime.fromtimestamp(mtime),
                    "age_hours": round((time.time() - mtime) / 3600, 1),
                    "query_info": query_info,
                    "processing_time": processing_time
                })
            except (OSError, IOError):
                continue
        
        # Sort by modification time (newest first)
        files_info.sort(key=lambda x: x["modified_time"], reverse=True)
        return files_info
    
    def clear_cache(self) -> Dict[str, Any]:
        """Clear all cache files"""
        cache_files = glob.glob(os.path.join(self.cache_dir, "*.pkl"))
        
        deleted_count = 0
        failed_count = 0
        total_size_freed = 0
        
        for cache_file in cache_files:
            try:
                file_size = os.path.getsize(cache_file)
                os.remove(cache_file)
                deleted_count += 1
                total_size_freed += file_size
            except Exception as e:
                failed_count += 1
                print(f"Failed to delete {cache_file}: {e}")
        
        return {
            "deleted_count": deleted_count,
            "failed_count": failed_count,
            "total_size_freed_mb": round(total_size_freed / (1024 * 1024), 2)
        }
    
    def clear_old_cache(self, days_old: int = 7) -> Dict[str, Any]:
        """Clear cache files older than specified days"""
        cache_files = glob.glob(os.path.join(self.cache_dir, "*.pkl"))
        cutoff_time = time.time() - (days_old * 24 * 3600)
        
        deleted_count = 0
        failed_count = 0
        total_size_freed = 0
        
        for cache_file in cache_files:
            try:
                mtime = os.path.getmtime(cache_file)
                if mtime < cutoff_time:
                    file_size = os.path.getsize(cache_file)
                    os.remove(cache_file)
                    deleted_count += 1
                    total_size_freed += file_size
            except Exception as e:
                failed_count += 1
                print(f"Failed to delete {cache_file}: {e}")
        
        return {
            "deleted_count": deleted_count,
            "failed_count": failed_count,
            "total_size_freed_mb": round(total_size_freed / (1024 * 1024), 2)
        }

def show_cache_management_page():
    """Display the cache management dashboard"""
    # Log cache management access
    try:
        from utils.usage_logger import log_analytics_access
        log_analytics_access("cache_management_access")
    except Exception:
        pass
    
    st.markdown("""
    <div style="text-align: center; padding: 2rem 0;">
        <h1>🗄️ Cache management</h1>
        <p style="color: #666; font-size: 1.1rem;">
            Manage search result caching and performance optimization
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    cache_manager = CacheManager()
    
    # Cache Status Section
    st.markdown("## 📊 Cache status")
    
    # Current cache setting
    current_cache_setting = st.session_state.get('use_cache_setting', True)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Cache toggle
        use_cache = st.toggle(
            "Enable search result caching",
            value=current_cache_setting,
            help="When enabled, search results are cached to improve performance for repeated queries"
        )
        
        if use_cache != current_cache_setting:
            st.session_state.use_cache_setting = use_cache
            # Update the backend cache setting if possible
            if 'backend' in st.session_state:
                st.session_state.backend.use_cache = use_cache
            
            # Log cache setting change
            try:
                from utils.usage_logger import log_analytics_access
                log_analytics_access("cache_setting_change", 
                                    export_type=f"cache_{'enabled' if use_cache else 'disabled'}")
            except Exception:
                pass
            
            if use_cache:
                st.success("✅ Cache enabled - search results will be cached for faster repeated queries")
            else:
                st.warning("⚠️ Cache disabled - all searches will hit the backend directly")
    
    with col2:
        status_color = "🟢" if use_cache else "🔴"
        status_text = "Active" if use_cache else "Disabled"
        st.markdown(f"**Cache Status:** {status_color} {status_text}")
    
    # Cache Statistics
    st.markdown("## 📈 Cache statistics")
    
    stats = cache_manager.get_cache_stats()
    
    if stats["total_files"] == 0:
        st.info("📭 No cache files found. Start using the search functionality to build up cache.")
    else:
        # Display key metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Cached searches", stats["total_files"])
        
        with col2:
            st.metric("Total cache size", f"{stats['total_size_mb']} MB")
        
        with col3:
            time_saved_formatted = f"{stats['estimated_time_saved']//60}m {stats['estimated_time_saved']%60}s"
            st.metric("Est. time saved", time_saved_formatted)
        
        with col4:
            st.metric("Avg file size", f"{stats['avg_file_size_kb']} KB")
        
        # Additional info
        col1, col2 = st.columns(2)
        
        with col1:
            if stats["oldest_file"]:
                st.markdown(f"**Oldest cache:** {stats['oldest_file'].strftime('%Y-%m-%d %H:%M')}")
        
        with col2:
            if stats["newest_file"]:
                st.markdown(f"**Newest cache:** {stats['newest_file'].strftime('%Y-%m-%d %H:%M')}")
    
    # Cache Management Actions
    st.markdown("## 🛠️ Cache management actions")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🗑️ Clear all cache", type="secondary", use_container_width=True):
            if stats["total_files"] > 0:
                with st.spinner("Clearing cache..."):
                    result = cache_manager.clear_cache()
                    
                    # Log cache clear action
                    try:
                        from utils.usage_logger import log_analytics_access
                        log_analytics_access("cache_clear", 
                                            export_type=f"clear_all_{result['deleted_count']}_files")
                    except Exception:
                        pass
                    
                    if result["deleted_count"] > 0:
                        st.success(f"✅ Cleared {result['deleted_count']} cache files "
                                 f"({result['total_size_freed_mb']} MB freed)")
                    
                    if result["failed_count"] > 0:
                        st.warning(f"⚠️ Failed to delete {result['failed_count']} files")
                    
                    st.rerun()
            else:
                st.info("No cache files to clear")
    
    with col2:
        if st.button("🧹 Clear old cache (7+ days)", type="secondary", use_container_width=True):
            with st.spinner("Clearing old cache..."):
                result = cache_manager.clear_old_cache(7)
                
                # Log old cache clear action
                try:
                    from utils.usage_logger import log_analytics_access
                    log_analytics_access("cache_clear", 
                                        export_type=f"clear_old_{result['deleted_count']}_files")
                except Exception:
                    pass
                
                if result["deleted_count"] > 0:
                    st.success(f"✅ Cleared {result['deleted_count']} old cache files "
                             f"({result['total_size_freed_mb']} MB freed)")
                else:
                    st.info("No old cache files found (7+ days)")
                
                if result["failed_count"] > 0:
                    st.warning(f"⚠️ Failed to delete {result['failed_count']} files")
                
                st.rerun()
    
    with col3:
        if st.button("🔄 Refresh stats", type="secondary", use_container_width=True):
            st.rerun()
    
    # Cache Performance Insights
    if stats["total_files"] > 0:
        st.markdown("## 💡 Performance insights")
        
        efficiency_score = min(100, (stats["total_files"] / 50) * 100)  # Assume 50 cached queries is good
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("**Cache efficiency insights:**")
            
            if efficiency_score >= 80:
                st.success("🎯 Excellent cache utilization! Your cache is helping performance significantly.")
            elif efficiency_score >= 50:
                st.info("👍 Good cache utilization. Consider using the application more to build up cache.")
            else:
                st.warning("📈 Low cache utilization. More usage will improve performance over time.")
            
            # Calculate cache hit potential
            if stats["estimated_time_saved"] > 300:  # 5 minutes
                st.success(f"⚡ Cache has saved approximately {stats['estimated_time_saved']//60} minutes of processing time!")
        
        with col2:
            st.metric("Cache efficiency", f"{efficiency_score:.0f}%")
    
    # Detailed Cache Files (expandable)
    if stats["total_files"] > 0:
        with st.expander(f"📄 View cache files details ({stats['total_files']} files)", expanded=False):
            files_info = cache_manager.get_cache_files_info()
            
            if files_info:
                # Create a table of cache files
                import pandas as pd
                
                df_data = []
                for file_info in files_info[:50]:  # Show first 50 files
                    df_data.append({
                        "Cache Key": file_info["cache_key"][:30] + "..." if len(file_info["cache_key"]) > 30 else file_info["cache_key"],
                        "Size (KB)": file_info["size_kb"],
                        "Age (hours)": file_info["age_hours"],
                        "Modified": file_info["modified_time"].strftime('%m/%d %H:%M'),
                        "Processing Time": file_info["processing_time"]
                    })
                
                df = pd.DataFrame(df_data)
                st.dataframe(df, use_container_width=True, hide_index=True)
                
                if len(files_info) > 50:
                    st.info(f"Showing first 50 files. Total: {len(files_info)} files")
            else:
                st.info("No cache file details available")
    
    # Cache Configuration Tips
    st.markdown("## ℹ️ Cache information")
    
    with st.expander("How caching works", expanded=False):
        st.markdown("""
        **Search Result Caching:**
        - When caching is enabled, search results are stored locally for identical queries
        - Cache keys are generated from query text, filters, and search parameters
        - Cached results are returned instantly without hitting the backend
        - Cache files are stored in the `cache/` directory as `.pkl` files
        
        **Performance Benefits:**
        - Dramatically faster response times for repeated searches
        - Reduced load on embedding and vector search services
        - Better user experience for common queries
        - Cost savings on API calls
        
        **Cache Management:**
        - Enable/disable caching without losing existing cache
        - Clear all cache to free up space
        - Remove old cache files automatically
        - Monitor cache usage and performance
        
        **When to Clear Cache:**
        - When document corpus has been updated
        - To free up disk space
        - When search algorithms have changed
        - Periodically for maintenance
        """)
