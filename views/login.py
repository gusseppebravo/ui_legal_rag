import streamlit as st

def show_login_page():
    """Display the login page"""
    st.markdown("""
    <div style="text-align: center; padding: 3rem 0;">
        <h1>🔐 Login</h1>
        <p style="color: #666; font-size: 1.1rem;">
            Please enter your credentials to access the contract intelligence system
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Center the login form
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        with st.container():
            st.markdown("### Enter credentials")
            
            # Login form
            with st.form("login_form"):
                username = st.text_input("Username", placeholder="Enter username")
                password = st.text_input("Password", type="password", placeholder="Enter password")
                submit_button = st.form_submit_button("Login", use_container_width=True, type="primary")
                
                if submit_button:
                    # Check admin credentials first
                    if (username == st.secrets["admin"]["username"] and 
                        password == st.secrets["admin"]["password"]):
                        
                        # Set admin authentication state
                        st.session_state.authenticated = True
                        st.session_state.is_admin = True
                        st.session_state.username = username
                        st.session_state.current_page = "analytics"
                        
                        # Log successful admin login
                        try:
                            from utils.usage_logger import log_authentication
                            log_authentication("login", username, is_admin=True, success=True)
                        except Exception:
                            pass
                        
                        st.success("✅ Admin login successful! Redirecting to analytics...")
                        st.rerun()
                        
                    # Check regular user credentials
                    elif (username == st.secrets["auth"]["username"] and 
                          password == st.secrets["auth"]["password"]):
                        
                        # Set regular user authentication state
                        st.session_state.authenticated = True
                        st.session_state.is_admin = False
                        st.session_state.username = username
                        st.session_state.current_page = "server_status"
                        
                        # Log successful user login
                        try:
                            from utils.usage_logger import log_authentication
                            log_authentication("login", username, is_admin=False, success=True)
                        except Exception:
                            pass
                        
                        st.success("✅ Login successful! Redirecting...")
                        st.rerun()
                    else:
                        # Log failed login attempt
                        try:
                            from utils.usage_logger import log_authentication
                            log_authentication("login", username, is_admin=False, success=False)
                        except Exception:
                            pass
                        st.error("❌ Invalid username or password")
            
            # Additional info
            st.markdown("---")
            st.info("💡 Contact your administrator for access credentials")

def check_authentication():
    """Check if user is authenticated"""
    return st.session_state.get('authenticated', False)

def logout():
    """Log out the current user"""
    # Log logout event
    try:
        from utils.usage_logger import log_authentication
        username = st.session_state.get('username', 'unknown')
        is_admin = st.session_state.get('is_admin', False)
        log_authentication("logout", username, is_admin=is_admin, success=True)
    except Exception:
        pass
    
    # Clear authentication state
    if 'authenticated' in st.session_state:
        del st.session_state.authenticated
    if 'username' in st.session_state:
        del st.session_state.username
    if 'is_admin' in st.session_state:
        del st.session_state.is_admin
    
    # Reset to login page
    st.session_state.current_page = "login"
    st.rerun()
