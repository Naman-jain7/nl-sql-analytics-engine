from datetime import datetime

from pydantic import BaseModel


class QueryRequest(BaseModel):
    dataset_id: int
    question: str

class SQLQuery(BaseModel):
    query: str
    is_valid: bool
    error: str | None = None

class QueryLog(BaseModel):
    id: int
    dataset_id: int
    question: str
    generated_sql: str
    execution_status: str        # success / failed
    error: str | None = None
    created_at: datetime