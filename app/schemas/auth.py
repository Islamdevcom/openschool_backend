from pydantic import BaseModel

class LoginRequest(BaseModel):
    email: str
    password: str
    
    class Config:
        extra = "ignore"