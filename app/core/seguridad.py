from jose import JWTError, jwt
from passlib.context import CryptContext

# Configuración de hashing
contexto_encriptacion = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verificar_contrasena(plana, encriptada):
    return contexto_encriptacion.verify(plana, encriptada)

def obtener_hash_contrasena(contrasena):
    return contexto_encriptacion.hash(contrasena)