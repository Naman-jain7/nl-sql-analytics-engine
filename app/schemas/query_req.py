from typing import Optional
from pydantic import BaseModel
from datetime import datetime

class QueryRequest(BaseModel):
    dataset_id: int
    question: str

class SQLQuery(BaseModel):
    query: str
    is_valid: bool
    error: Optional[str] = None

class QueryLog(BaseModel):
    id: int
    dataset_id: int
    question: str
    generated_sql: str
    execution_status: str        # success / failed
    error: Optional[str] = None
    created_at: datetime