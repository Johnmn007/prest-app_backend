import bcrypt
from datetime import datetime, timedelta
from typing import Optional
from jose import jwt
from app.config.settings import settings

# Eliminamos CryptContext de passlib porque genera conflictos en Python 3.12+ 
# Usamos bcrypt directamente para máxima compatibilidad.

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifica si la contraseña plana coincide con el hash almacenado.
    """
    try:
        # bcrypt requiere bytes, codificamos los strings
        return bcrypt.checkpw(
            plain_password.encode('utf-8'), 
            hashed_password.encode('utf-8')
        )
    except Exception as e:
        print(f"Error verificando password: {e}")
        return False

def get_password_hash(password: str) -> str:
    """
    Genera un hash seguro usando bcrypt.
    """
    # Generar sal y hashear
    pwd_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(pwd_bytes, salt)
    return hashed.decode('utf-8')

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Crea un token JWT firmado.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        # settings.JWT_EXPIRE debe ser un número entero (minutos)
        expire = datetime.utcnow() + timedelta(minutes=int(settings.JWT_EXPIRE))
    
    to_encode.update({"exp": expire})
    
    # settings.JWT_SECRET es la variable configurada en Railway
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET, algorithm="HS256")
    return encoded_jwt

def decode_access_token(token: str) -> dict:
    """
    Decodifica y valida un token JWT.
    """
    return jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])