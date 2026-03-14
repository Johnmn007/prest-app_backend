import bcrypt
from datetime import datetime, timedelta
from typing import Optional
from jose import jwt
from app.config.settings import settings

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        # Forzamos a bytes para evitar errores de codificación
        return bcrypt.checkpw(
            plain_password.encode('utf-8'), 
            hashed_password.encode('utf-8')
        )
    except Exception:
        return False

def get_password_hash(password: str) -> str:
    pwd_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(pwd_bytes, salt)
    return hashed.decode('utf-8')

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    
    # Aseguramos que expire sea un entero
    try:
        expire_minutes = int(settings.JWT_EXPIRE)
    except:
        expire_minutes = 10080 # 1 semana por defecto

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=expire_minutes)
    
    to_encode.update({"exp": expire})
    
    # Aseguramos que JWT_SECRET sea string y no esté vacío
    secret_key = str(settings.JWT_SECRET)
    
    # El error suele estar aquí si la librería jose no recibe los tipos exactos
    encoded_jwt = jwt.encode(to_encode, secret_key, algorithm="HS256")
    return str(encoded_jwt)

def decode_access_token(token: str) -> dict:
    return jwt.decode(str(token), str(settings.JWT_SECRET), algorithms=["HS256"])