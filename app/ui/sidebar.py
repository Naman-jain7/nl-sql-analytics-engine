import streamlit as st

def render_sidebar():
    """Render the QuerySight sidebar UI."""
    with st.sidebar:
        st.image("https://img.icons8.com/isometric/100/database.png", width=80) 
        st.markdown("### **Control Panel**")
        st.divider()

        # Database Connection
        st.markdown("#### 🔗 Database Connection")
        db_type = st.selectbox("Engine", ["SQLite", "PostgreSQL (Future)", "MySQL (Future)"], index=0)
        
        if db_type == "SQLite":
            db_path = st.text_input("Database Path", value="data/querysight.db")
            if st.button("Connect", use_container_width=True):
                st.session_state.db_connected = True
                st.success("Connected to SQLite!")
        
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
