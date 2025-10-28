from sqlalchemy.orm import Session
from .. import models
from ..schemas.registration_request import RegistrationRequestCreate

def create_request(db: Session, request: RegistrationRequestCreate):
    db_request = models.RegistrationRequest(
        full_name=request.full_name,
        email=request.email,
        password=request.password,
        role=request.role,
        school_id=request.school_id,
    )
    db.add(db_request)
    db.commit()
    db.refresh(db_request)
    return db_request
