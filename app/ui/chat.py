import streamlit as st
import pandas as pd
from app.core.sql_gen import generate_sql
from app.db.sqlite_db import execute_query

def render_chat():
    """Render the main chat interface and schema builder."""

    # 1. Schema Builder Section (Crucial Requirement)
    with st.expander("🛠️ Schema Builder", expanded=not st.session_state.schema):
        st.markdown("##### Define your database structure")

        # Table Name Input
        table_name = st.text_input("Table Name", placeholder="e.g., sales_data")

        # Column definitions using data_editor for premium feel
        if "temp_cols" not in st.session_state:
            st.session_state.temp_cols = [
                {
                    "Column Name": "id",
                    "Type": "INTEGER",
                    "PK": True,
                    "Nullable": False,
                    "Default": "",
                },
                {
                    "Column Name": "created_at",
                    "Type": "TIMESTAMP",
                    "PK": False,
                    "Nullable": True,
                    "Default": "CURRENT_TIMESTAMP",
                },
            ]

        def handle_editor_change():
            """Callback to enforce single PK logic."""
            state = st.session_state.schema_editor
            
            # 1. Update the underlying data with all changes first
            df = pd.DataFrame(st.session_state.temp_cols)
            
            # Handle deleted rows
            if state["deleted_rows"]:
                df = df.drop(state["deleted_rows"]).reset_index(drop=True)
                
            # Handle added rows
            for added in state["added_rows"]:
                new_row = {
                    "Column Name": added.get("Column Name", ""),
                    "Type": added.get("Type", "TEXT"),
                    "PK": added.get("PK", False),
                    "Nullable": added.get("Nullable", True),
                    "Default": added.get("Default", "")
                }
                df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                
            # Handle edited rows
            pk_just_selected_idx = -1
            for idx, edits in state["edited_rows"].items():
                idx_int = int(idx)
                for col, val in edits.items():
                    df.at[idx_int, col] = val
                    if col == "PK" and val == True:
                        pk_just_selected_idx = idx_int

            # 2. Enforce single PK rule: If a new row is selected as PK, unselect all others
            if pk_just_selected_idx != -1:
                for i in range(len(df)):
                    if i != pk_just_selected_idx:
                        df.at[i, "PK"] = False
                # Also ensure PK column is not nullable
                df.at[pk_just_selected_idx, "Nullable"] = False

            st.session_state.temp_cols = df.to_dict("records")

        edited_df = st.data_editor(
            pd.DataFrame(st.session_state.temp_cols),
            num_rows="dynamic",
            column_config={
                "Type": st.column_config.SelectboxColumn(
                    "Data Type",
                    options=[
                        "INTEGER",
                        "TEXT",
                        "FLOAT",
                        "BOOLEAN",
                        "DATE",
                        "TIMESTAMP",
                        "DECIMAL",
                    ],
                    required=True,
                ),
                "PK": st.column_config.CheckboxColumn("Primary Key"),
                "Nullable": st.column_config.CheckboxColumn("Nullable"),
            },
            width='stretch',
            key="schema_editor",
            on_change=handle_editor_change
        )

        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button("Save Table Schema", type="primary"):
                if not table_name:
                    st.error("Please provide a table name.")
                else:
                    # Final validation before saving
                    pk_count = sum(1 for _, row in edited_df.iterrows() if row["PK"])
                    if pk_count > 1:
                        st.error("Only one column can be selected as primary key.")
                    elif pk_count == 0:
                        st.warning("No primary key defined. Some features might not work correctly.")
                        
                    new_schema = []
                    error_found = False
                    for _, row in edited_df.iterrows():
                        col_name = row["Column Name"]
                        is_pk = row["PK"]
                        is_nullable = row["Nullable"]
                        
                        if is_pk and is_nullable:
                            st.error(f"Primary key '{col_name}' cannot be nullable.")
                            error_found = True
                            break
                            
                        new_schema.append({
                            "name": col_name,
                            "type": row["Type"],
                            "pk": is_pk,
                            "nullable": is_nullable,
                            "default": row["Default"],
                        })
                    
                    if not error_found:
                        st.session_state.schema[table_name] = new_schema
                        st.success(f"Schema for '{table_name}' saved!")
                        st.rerun()
        with col2:
            st.caption("Double-click cells to edit. Use '+' to add rows. Only one Primary Key allowed.")

    st.divider()

    # 2. Chat Display
    chat_container = st.container(height=500)
    with chat_container:
        if not st.session_state.messages:
            st.info(
                "👋 Welcome to QuerySight! Start by defining a schema or asking a question about your data."
            )

        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
                if "sql" in message:
                    st.code(message["sql"], language="sql")
                if "data" in message:
                    st.dataframe(message["data"], width='stretch')

    # 3. Chat Input
    if prompt := st.chat_input("Ask a question about your data..."):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})

        # Display user message and generate response
        with chat_container:
            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                if not st.session_state.schema:
                    st.warning("Please define a schema first so I can generate accurate SQL.")
                else:
                    response_placeholder = st.empty()
                    response_placeholder.markdown("🔍 *Analyzing schema and generating query...*")
                    
                    # 1. Generate SQL using Qwen + LoRA
                    generated_sql = generate_sql(prompt, st.session_state.schema)
                    
                    # 2. Execute the generated SQL
                    df, error = execute_query(generated_sql)
                    
                    if error:
                        response_content = f"I generated the following SQL, but encountered an error during execution: \n\n`{error}`"
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": response_content,
                            "sql": generated_sql
                        })
                    else:
                        response_content = "I've generated and executed a query to answer your question."
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": response_content,
                            "sql": generated_sql,
                            "data": df
                        })
                    
                    st.rerun()
