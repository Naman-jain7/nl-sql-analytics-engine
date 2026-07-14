import streamlit as st
import os
from dotenv import load_dotenv

load_dotenv()
DATA_DIR=os.getenv('DATA_DIR')
MYSQL_HOST=os.getenv('MYSQL_HOST')
MYSQL_USER=os.getenv('MYSQL_USER')
MYSQL_PORT=os.getenv('MYSQL_PORT')
LLM_MODEL_NAME = os.getenv('LLM_MODEL_NAME')

def render_sidebar():
    """Render the QuerySight sidebar UI."""
    with st.sidebar:
        st.image("https://img.icons8.com/isometric/100/database.png", width=80) 
        st.markdown("### **Control Panel**")
        st.divider()

        # Database Connection
        st.markdown("#### 🔗 Database Connection")
        db_type = st.selectbox("Engine", ["SQLite", "MySQL"], index=0)
        st.session_state.db_engine = db_type
        
        if db_type == "SQLite":
            db_path = st.text_input("Database Path", value=DATA_DIR)
            st.session_state.db_config = {"path": db_path}
            if st.button("Connect", use_container_width=True):
                st.session_state.db_connected = True
                st.success("Connected to SQLite!")
        
        elif db_type == "MySQL":
            col1, col2 = st.columns(2)
            with col1:
                host = st.text_input("Host", value=MYSQL_HOST)
                user = st.text_input("User", value=MYSQL_USER)
            with col2:
                port = st.text_input("Port", value=MYSQL_PORT)
                db_name = st.text_input("Database")
            
            password = st.text_input("Password", type="password")
            
            st.session_state.db_config = {
                "host": host,
                "port": port,
                "user": user,
                "password": password,
                "database": db_name
            }
            
            if st.button("Connect", use_container_width=True):
                # We can add a ping test here later
                st.session_state.db_connected = True
                st.success("Configured MySQL!")
        
        st.divider()
        
        # Model Configuration
        st.markdown("#### 🧠 Model Engine")
        model_choice = st.selectbox(
            "Select Generator", 
            ["Qwen 2.5 (Local LoRA)", LLM_MODEL_NAME],
            index=0
        )
        st.session_state.selected_model = model_choice
        
        st.divider()

        # Schema Status
        st.markdown("#### 📊 Schema Intelligence")
        if not st.session_state.schema:
            st.info("No tables defined yet. Use the Chat interface to define your schema.")
        else:
            for table_name in st.session_state.schema:
                with st.expander(f"📦 {table_name}"):
                    cols = st.session_state.schema[table_name]
                    for col in cols:
                        st.text(f"{col['name']} ({col['type']})")

        st.divider()
        
        # System status
        st.markdown("#### ⚙️ System Status")
        st.status("Model: Qwen2.5-3B Optimized", state="complete")
        st.status("Inference: Local Ollama", state="complete")

        st.divider()
        if st.button("🗑️ Clear Chat", use_container_width=True):
            st.session_state.messages = []
            st.rerun()

        st.caption("v0.1.0-alpha | QuerySight Engineering")
