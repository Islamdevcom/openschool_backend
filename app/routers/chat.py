from fastapi import APIRouter

router = APIRouter()

@router.get("/test")
def test_users():
    return {"msg": "Users router работает"}
