from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from app.schemas.registration_request import RegistrationRequestCreate, RegistrationRequestOut
from app.models.registration_request import RegistrationRequest
from app.models.school import School

router = APIRouter(prefix="/register-request", tags=["Registration Requests"])

@router.post("/", response_model=RegistrationRequestOut)
def create_registration_request(request_data: RegistrationRequestCreate, db: Session = Depends(get_db)):
    school = db.query(School).filter(School.id == request_data.school_id).first()
    if not school:
        raise HTTPException(status_code=404, detail="Школа не найдена")

    # можно проверку на дубликаты email сделать при желании

    new_request = RegistrationRequest(**request_data.dict())
    db.add(new_request)
    db.commit()
    db.refresh(new_request)
    return new_request
