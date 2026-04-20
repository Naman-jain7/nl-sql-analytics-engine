import os
import sys

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

import streamlit as st  # noqa: E402
from app.ui.sidebar import render_sidebar  # noqa: E402
from app.ui.chat import render_chat  # noqa: E402


def init_session_state():
    """Initialize session state variables."""
    if "messages" not in st.session_state:
        st.session_state.messages = []

    if "schema" not in st.session_state:
        st.session_state.schema = {}  # Table name -> list of col definitions

    if "db_connected" not in st.session_state:
        st.session_state.db_connected = False

    if "db_engine" not in st.session_state:
        st.session_state.db_engine = "SQLite"
    
    if "db_config" not in st.session_state:
        st.session_state.db_config = {"path": "data/querysight.db"}


def apply_custom_css():
    """Apply premium styling with vanilla CSS."""
    st.markdown(
        """
        <style>
        /* Modern Gradient Background for Sidebar */
        [data-testid="stSidebar"] {
            background-image: linear-gradient(180deg, #1e1e2f 0%, #121212 100%);
            border-right: 1px solid rgba(255, 255, 255, 0.1);
        }

        /* Glassmorphism for cards/containers */
        .stChatMessage {
            background: rgba(255, 255, 255, 0.03) !important;
            border: 1px solid rgba(255, 255, 255, 0.05);
            border-radius: 12px !important;
            margin-bottom: 1rem !important;
            backdrop-filter: blur(10px);
        }

        /* Modern Headers */
        h1, h2, h3 {
            font-family: 'Inter', sans-serif;
            background: linear-gradient(90deg, #00d2ff 0%, #3a7bd5 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-weight: 700 !important;
        }

        /* Custom Button Styling */
        .stButton>button {
            border-radius: 8px;
            background: linear-gradient(90deg, #4facfe 0%, #00f2fe 100%);
            color: white;
            border: none;
            transition: all 0.3s ease;
            font-weight: 600;
        }

        .stButton>button:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 15px rgba(79, 172, 254, 0.4);
        }

        /* Text Input Styling */
        .stTextInput>div>div>input {
            border-radius: 8px;
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        /* Hide Streamlit branding */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        </style>
    """,
        unsafe_allow_html=True,
    )


def main():
    st.set_page_config(
        page_title="QuerySight | NL SQL Analytics",
        page_icon="🔍",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    init_session_state()
    apply_custom_css()

    # Main Layout
    render_sidebar()

    st.title("🔍 QuerySight")
    st.caption("Transform natural language into data insights with precision.")

    render_chat()


if __name__ == "__main__":
    main()
