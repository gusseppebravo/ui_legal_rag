import streamlit as st
import requests
import time
from typing import Dict, Any

# API Configuration
API_BASE_URL = "https://zgggzg2iqg.execute-api.us-east-1.amazonaws.com/dev"
API_KEY = "2jIpWCyNRg3Y8lkbmWG0tkyXwYlJn5QaZ1F3yKf7"
MODEL_NAME = "e5_mistral_embed_384"

def check_server_health() -> Dict[str, Any]:
    """Check if the embedding server is healthy"""
    try:
        response = requests.get(
            f"{API_BASE_URL}/health",
            headers={"x-api-key": API_KEY},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            return {
                "status": "healthy",
                "data": data,
                "status_code": response.status_code
            }
        else:
            return {
                "status": "unhealthy",
                "error": f"HTTP {response.status_code}",
                "status_code": response.status_code
            }
    except requests.exceptions.RequestException as e:
        return {
            "status": "error",
            "error": str(e),
            "status_code": None
        }

def cold_start_server() -> Dict[str, Any]:
    """Send a test query to cold start the embedding server"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/get_embeddings",
            headers={
                "Content-Type": "application/json",
                "x-api-key": API_KEY
            },
            json={
                "model_name": MODEL_NAME,
                "texts": ["test_query"]
            },
            timeout=30
        )
        
        return {
            "status": "success" if response.status_code == 200 else "failed",
            "status_code": response.status_code,
            "response": response.json() if response.status_code == 200 else response.text
        }
    except requests.exceptions.RequestException as e:
        return {
            "status": "error",
            "error": str(e),
            "status_code": None
        }

def show_server_status_page():
    """Display the server status checking page with automatic checking"""
    st.markdown("""
    <div style="text-align: center; padding: 2rem 0;">
        <h1>🖥️ Server status</h1>
        <p style="color: #666; font-size: 1.1rem;">
            Checking embedding server availability...
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Initialize session state for automatic checking
    if 'server_check_started' not in st.session_state:
        st.session_state.server_check_started = False
        st.session_state.cold_start_attempted = False
        st.session_state.check_count = 0
        st.session_state.last_check_time = 0
    
    # Status containers
    status_container = st.container()
    message_container = st.container()
    action_container = st.container()
    
    # Auto-start the checking process
    current_time = time.time()
    if not st.session_state.server_check_started or (current_time - st.session_state.last_check_time > 60):
        st.session_state.server_check_started = True
        st.session_state.last_check_time = current_time
        
        with status_container:
            with st.spinner("Checking server health..."):
                time.sleep(1)  # Brief pause for UI
                health_result = check_server_health()
                st.session_state.check_count += 1
                
                if health_result["status"] == "healthy":
                    st.success("✅ Embedding server is ready!")
                    
                    # Display server info
                    if "data" in health_result:
                        data = health_result["data"]
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            st.metric("Status", data.get("status", "N/A"))
                        with col2:
                            st.metric("Model", data.get("model_name", "N/A"))
                        with col3:
                            st.metric("HTTP Code", health_result["status_code"])
                    
                    # Mark server as ready and automatically continue
                    st.session_state.server_ready = True
                    st.info("🚀 Launching application...")
                    time.sleep(2)  # Brief pause to show the message
                    st.session_state.current_page = "search"
                    st.rerun()
                
                else:
                    st.error(f"❌ Server not ready: {health_result.get('error', 'Unknown error')}")
                    
                    # Try cold start if not attempted yet
                    if not st.session_state.cold_start_attempted:
                        st.session_state.cold_start_attempted = True
                        
                        with message_container:
                            st.warning("⚡ Attempting to start server...")
                            
                            with st.spinner("Sending cold start request..."):
                                cold_start_result = cold_start_server()
                                
                                if cold_start_result["status"] == "success":
                                    st.info("Cold start request sent. Server is warming up...")
                                    st.info("⏱️ This may take 5-10 minutes. Auto-checking every minute...")
                                else:
                                    st.error(f"Failed to send cold start request: {cold_start_result.get('error', 'Unknown error')}")
                    
                    else:
                        # Show waiting message
                        with message_container:
                            st.info("⏱️ Waiting for server to start...")
                            st.write(f"Check attempt: {st.session_state.check_count}")
                    
                    # Show spinner and countdown for 1 minute
                    with st.spinner("Server starting... Next check in 1 minute"):
                        for i in range(60, 0, -1):
                            time.sleep(1)
                    
                    # Auto-refresh after 1 minute
                    st.rerun()
        
        # Manual refresh option
        with action_container:
            st.markdown("---")
            if st.button("🔄 Check now", use_container_width=True, type="primary"):
                st.session_state.last_check_time = 0  # Force immediate recheck
                st.rerun()
