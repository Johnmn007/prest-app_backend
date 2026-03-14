# from fastapi import APIRouter, Depends, HTTPException, status
# from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
# from sqlalchemy.orm import Session
# from datetime import timedelta
# from jose import JWTError
# from app.database.connection import get_db
# from app.schemas.user_schema import UserCreate, UserResponse, Token, TokenData
# from app.services.auth_service import get_user_by_email, create_user
# from app.core.security import verify_password, create_access_token, decode_access_token
# from app.config.settings import settings

# router = APIRouter(prefix="/auth", tags=["Auth"])

# oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

# def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
#     credentials_exception = HTTPException(
#         status_code=status.HTTP_401_UNAUTHORIZED,
#         detail="Could not validate credentials",
#         headers={"WWW-Authenticate": "Bearer"},
#     )
#     try:
#         payload = decode_access_token(token)
#         email: str = payload.get("email")
#         if email is None:
#             raise credentials_exception
#         token_data = TokenData(email=email)
#     except JWTError:
#         raise credentials_exception
#     user = get_user_by_email(db, email=token_data.email)
#     if user is None:
#         raise credentials_exception
#     return user

# @router.post("/register", response_model=UserResponse)
# def register(user: UserCreate, db: Session = Depends(get_db)):
#     db_user = get_user_by_email(db, email=user.email)
#     if db_user:
#         raise HTTPException(status_code=400, detail="Email already registered")
#     return create_user(db=db, user=user)

# @router.post("/login", response_model=Token)
# def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
#     user = get_user_by_email(db, email=form_data.username)
#     if not user or not verify_password(form_data.password, user.password_hash):
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Incorrect email or password",
#             headers={"WWW-Authenticate": "Bearer"},
#         )
#     access_token_expires = timedelta(minutes=settings.JWT_EXPIRE)
#     access_token = create_access_token(
#         data={"email": user.email, "role": user.role}, expires_delta=access_token_expires
#     )
#     return {"access_token": access_token, "token_type": "bearer"}

# @router.get("/me", response_model=UserResponse)
# def read_users_me(current_user: UserResponse = Depends(get_current_user)):
#     return current_user



from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
import traceback

from app.database.connection import get_db
from app.core.security import verify_password, create_access_token
from app.config.settings import settings
from app.schemas.user import Token
from app.api.clients import get_user_by_email # Asegúrate que esta ruta de import sea correcta en tu proyecto

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post("/login", response_model=Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    print(f"DEBUG: Iniciando login para {form_data.username}")
    try:
        # 1. Buscar usuario
        user = get_user_by_email(db, email=form_data.username)
        if not user:
            print("DEBUG: Usuario no encontrado")
            raise HTTPException(status_code=401, detail="Correo o contraseña incorrectos")
        
        # 2. Verificar Password
        try:
            is_valid = verify_password(form_data.password, user.password_hash)
            print(f"DEBUG: Resultado validacion password: {is_valid}")
        except Exception as e:
            print(f"DEBUG: Error en verify_password: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error en validación de hash: {str(e)}")

        if not is_valid:
            raise HTTPException(status_code=401, detail="Correo o contraseña incorrectos")

        # 3. Generar Token
        try:
            access_token_expires = timedelta(minutes=int(settings.JWT_EXPIRE))
            access_token = create_access_token(
                data={"sub": user.email, "role": user.role}, 
                expires_delta=access_token_expires
            )
            print("DEBUG: Token generado con éxito")
        except Exception as e:
            print(f"DEBUG: Error en create_access_token: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error al generar token (Variable JWT_SECRET?): {str(e)}")

        return {"access_token": access_token, "token_type": "bearer"}

    except HTTPException as he:
        raise he
    except Exception as e:
        trace = traceback.format_exc()
        print(f"DEBUG: Error critico: {trace}")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)} | Trace: {trace}")

@router.get("/me")
def read_users_me():
    return {"status": "ok"}