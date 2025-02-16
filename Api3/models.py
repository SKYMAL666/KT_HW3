from sqlmodel import SQLModel, Field
from datetime import datetime
from typing import Optional
import uuid

class FileInfo(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True, index=True)
    file_type: str
    file_size: int
    file_path: str
    upload_time: datetime = Field(default_factory=datetime.utcnow)