import os

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from app.core.llm import generate_with_ollama
from app.core.sql_gen import generate_sql
from app.db.sqlite_db import create_table, execute_query
from app.schemas.table import ColumnSchema, TableSchema

load_dotenv()

LLM_MODEL_NAME = os.getenv('LLM_MODEL_NAME')

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
            df = pd.DataFrame(st.session_state.temp_cols)
            
            if state["deleted_rows"]:
                df = df.drop(state["deleted_rows"]).reset_index(drop=True)
                
            for added in state["added_rows"]:
                new_row = {
                    "Column Name": added.get("Column Name", ""),
                    "Type": added.get("Type", "TEXT"),
                    "PK": added.get("PK", False),
                    "Nullable": added.get("Nullable", True),
                    "Default": added.get("Default", "")
                }
                df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                
            pk_just_selected_idx = -1
            for idx, edits in state["edited_rows"].items():
                idx_int = int(idx)
                for col, val in edits.items():
                    df.at[idx_int, col] = val
                    if col == "PK" and val:
                        pk_just_selected_idx = idx_int

            if pk_just_selected_idx != -1:
                for i in range(len(df)):
                    if i != pk_just_selected_idx:
                        df.at[i, "PK"] = False
                df.at[pk_just_selected_idx, "Nullable"] = False

            st.session_state.temp_cols = df.to_dict("records")

        edited_df = st.data_editor(
            pd.DataFrame(st.session_state.temp_cols),
            num_rows="dynamic",
            column_config={
                "Type": st.column_config.SelectboxColumn(
                    "Data Type",
                    options=["INTEGER", "TEXT", "FLOAT", "BOOLEAN", "DATE", "TIMESTAMP", "DECIMAL"],
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
                    pk_count = sum(1 for _, row in edited_df.iterrows() if row["PK"])
                    if pk_count > 1:
                        st.error("Only one column can be selected as primary key.")
                    elif pk_count == 0:
                        st.warning("No primary key defined.")
                        
                    new_schema_data = []
                    col_schemas = []
                    error_found = False
                    for _, row in edited_df.iterrows():
                        col_name = row["Column Name"]
                        is_pk = row["PK"]
                        is_nullable = row["Nullable"]
                        
                        if is_pk and is_nullable:
                            st.error(f"Primary key '{col_name}' cannot be nullable.")
                            error_found = True
                            break
                            
                        new_schema_data.append({
                            "name": col_name, "type": row["Type"], "pk": is_pk, "nullable": is_nullable, "default": row["Default"]
                        })
                        
                        col_schemas.append(ColumnSchema(
                            name=col_name, dtype=row["Type"], pk=is_pk, nullable=is_nullable, default_value=row["Default"]
                        ))
                    
                    if not error_found:
                        physical_schema = TableSchema(table_name=table_name, columns=col_schemas)
                        if create_table(physical_schema):
                            st.session_state.schema[table_name] = new_schema_data
                            st.success(f"Table '{table_name}' created successfully!")
                            st.rerun()
                        else:
                            st.error("Failed to create table. Check logs.")
                            
        with col2:
            st.caption("Double-click cells to edit. Use '+' to add rows.")

    st.divider()

    # 2. Chat Display
    chat_container = st.container(height=450)
    with chat_container:
        if not st.session_state.messages:
            st.info("👋 Welcome to QuerySight!")

        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
                if "sql" in message:
                    st.code(message["sql"], language="sql")
                if "data" in message:
                    st.dataframe(message["data"], width='stretch')

    if "selected_model" not in st.session_state:
        st.session_state.selected_model = "Qwen 2.5 (Local LoRA)"

    # 3. Chat Input
    if prompt := st.chat_input("Ask a question about your data..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with chat_container:
            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                if not st.session_state.schema:
                    st.warning("Please define a schema first.")
                else:
                    with st.spinner(f"Generating query using {st.session_state.selected_model}..."):
                        explanation = ""
                        if st.session_state.selected_model == "Qwen 2.5 (Local LoRA)":
                            generated_sql = generate_sql(prompt, st.session_state.schema)
                        else:
                            generated_sql, explanation = generate_with_ollama(
                                prompt, st.session_state['schema']
                            )
                        df, error = execute_query(generated_sql)
                    
                    if error:
                        st.session_state['messages'].append({
                            "role": "assistant", "content": f"Error: `{error}`", "sql": generated_sql, "explanation": explanation
                        })
                    else:
                        content = f"**Explanation**: {explanation}\n\nQuery results:" if explanation else "Results:"
                        st.session_state.messages.append({
                            "role": "assistant", "content": content, "sql": generated_sql, "data": df, "explanation": explanation
                        })
                    st.rerun()
