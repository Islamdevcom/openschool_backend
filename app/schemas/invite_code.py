from pydantic import BaseModel
from datetime import datetime

class InviteCodeCreate(BaseModel):
    pass  # генерим код на сервере

class InviteCodeUse(BaseModel):
    code: str

class InviteCodeResponse(BaseModel):
    code: str
    created_at: datetime

    class Config:
        from_attributes = True  # ✅ Pydantic v2
