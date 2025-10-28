from passlib.context import CryptContext

# создаём контекст для хеширования
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# хеширование пароля при регистрации
def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

# проверка пароля при логине
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)
