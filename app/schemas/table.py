from typing import List, Optional
from pydantic import BaseModel

class ColumnSchema(BaseModel):
    name: str
    dtype: str
    nullable: bool
    pk: bool = False
    default_value: Optional[str] = None


class TableSchema(BaseModel):
    table_name: str
    columns: List[ColumnSchema]