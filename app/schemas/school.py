from pydantic import BaseModel


class SchoolCreate(BaseModel):
    name: str
    code: str


class SchoolOut(BaseModel):
    id: int
    name: str
    code: str

    class Config:
        orm_mode = True  # позволяет возвращать из SQLAlchemy-моделей
