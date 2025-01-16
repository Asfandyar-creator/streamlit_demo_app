import streamlit as st
import sqlite3
import os
import bcrypt
from email_validator import validate_email, EmailNotValidError

# Set the page configuration
st.set_page_config(page_title="DataChat", page_icon=":brain:", layout="wide")

# Hide the default Streamlit navigation menu
hide_streamlit_style = """
<style>
#MainMenu {visibility: hidden;}
div[data-testid="stSidebarNav"] {display: none;}
</style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# Database setup
def init_db():
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            username TEXT NOT NULL,
            email TEXT PRIMARY KEY,
            password TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def add_user(username, email, hashed_password):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (username, email, password) VALUES (?, ?, ?)", 
                  (username, email, hashed_password))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        conn.close()
        return False

def validate_user(email, password):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("SELECT username, password FROM users WHERE email = ?", (email,))
    user = c.fetchone()
    conn.close()
    
    if not user:
        return "email_not_found", None
    
    if bcrypt.checkpw(password.encode('utf-8'), user[1].encode('utf-8')):
        return "success", user[0]
    return "invalid_password", None

# Initialize the database
init_db()

# Initialize session states
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = None
if "current_page" not in st.session_state:
    st.session_state.current_page = "home"

# Authentication page
def show_auth_page():
    st.title("Welcome to DataChat!")
    
    login_tab, signup_tab = st.tabs(["Login", "Signup"])
    
    with login_tab:
        st.subheader("Login")
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_password")
        
        if st.button("Login"):
            status, username = validate_user(email, password)
            
            if status == "success":
                st.session_state.logged_in = True
                st.session_state.username = username
                st.success(f"Welcome back, {username}!")
                st.rerun()
            elif status == "email_not_found":
                st.warning("No account found with this email. Please sign up first.")
            elif status == "invalid_password":
                st.error("Incorrect password. Please try again.")
    
    with signup_tab:
        st.subheader("Signup")
        new_username = st.text_input("Username", key="signup_username")
        new_email = st.text_input("Email", key="signup_email")
        new_password = st.text_input("Password", type="password", key="signup_password")
        
        if st.button("Signup"):
            try:
                valid_email = validate_email(new_email).email
                hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                if add_user(new_username, valid_email, hashed_password):
                    st.success("Signup successful! You can now log in.")
                else:
                    st.error("Email already exists. Please move to login.")
            except EmailNotValidError as e:
                st.error(f"Invalid email address: {str(e)}")

# Main app logic
if not st.session_state.logged_in:
    show_auth_page()
else:
    # Sidebar navigation for authenticated users
    st.sidebar.success(f"Logged in as: {st.session_state.username}")
    st.sidebar.title("Navigation")

    # Define available pages and their file paths
    pages = {
        "Home": "home",
        "Business Problem Extractor": "business",
        "Teacher Agent": "teacher",
        "Teacher Assistant Agent": "teacher_assistant"
    }

    # Navigation radio buttons
    selected_page = st.sidebar.radio("Go to:", list(pages.keys()))
    st.session_state.current_page = selected_page

    # Display selected page content only if logged in
    if selected_page == "Home":
        st.header("Welcome to DataChat Home Page!")
        st.write("You are logged in and can now explore the tools.")
    else:
        page_file = f"pages/{pages[selected_page]}.py"
        if os.path.exists(page_file):
            with open(page_file, encoding="utf-8") as f:
                exec(f.read(), globals())
        else:
            st.error(f"The page file '{page_file}' was not found.")

    # Logout button
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.username = None
        st.session_state.current_page = "home"
        st.rerun()
