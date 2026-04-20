import streamlit as st

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
            db_path = st.text_input("Database Path", value="data/querysight.db")
            st.session_state.db_config = {"path": db_path}
            if st.button("Connect", use_container_width=True):
                st.session_state.db_connected = True
                st.success("Connected to SQLite!")
        
        elif db_type == "MySQL":
            col1, col2 = st.columns(2)
            with col1:
                host = st.text_input("Host", value="localhost")
                user = st.text_input("User", value="root")
            with col2:
                port = st.text_input("Port", value="3306")
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
            ["Qwen 2.5 (Local LoRA)", "Ministral-3:3B"],
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
