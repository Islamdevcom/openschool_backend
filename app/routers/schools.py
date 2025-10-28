from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from app.models.school import School
from app.schemas.school import SchoolCreate, SchoolOut
from pydantic import BaseModel


router = APIRouter()

@router.post("/", response_model=SchoolOut)
def create_school(school_data: SchoolCreate, db: Session = Depends(get_db)):
    existing = db.query(School).filter(School.code == school_data.code).first()
    if existing:
        raise HTTPException(status_code=400, detail="Школа с таким кодом уже существует")

    new_school = School(**school_data.dict())
    db.add(new_school)
    db.commit()
    db.refresh(new_school)
    return new_school

@router.get("/", response_model=list[SchoolOut])
def get_all_schools(db: Session = Depends(get_db)):
    return db.query(School).all()

class SchoolCodeRequest(BaseModel):
    code: str
@router.post("/verify-code")
def verify_code(request: SchoolCodeRequest, db: Session = Depends(get_db)):
    school = db.query(School).filter(School.code == request.code).first()
    if not school:
        raise HTTPException(status_code=404, detail="Школа не найдена")
    
    return {"school_id": school.id}