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




import traceback
from fastapi import HTTPException

@router.post("/login", response_model=Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    try:
        user = get_user_by_email(db, email=form_data.username)
        if not user:
            raise HTTPException(status_code=401, detail="Usuario no encontrado")
        
        # Punto crítico 1: Bcrypt
        try:
            is_valid = verify_password(form_data.password, user.password_hash)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Fallo en Bcrypt: {str(e)}")

        if not is_valid:
            raise HTTPException(status_code=401, detail="Contraseña incorrecta")

        # Punto crítico 2: Generación de Token
        try:
            access_token_expires = timedelta(minutes=int(settings.JWT_EXPIRE))
            access_token = create_access_token(
                data={"email": user.email, "role": user.role}, 
                expires_delta=access_token_expires
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Fallo en JWT (Secret/Expire): {str(e)}")

        return {"access_token": access_token, "token_type": "bearer"}

    except HTTPException as he:
        raise he
    except Exception as e:
        # Esto nos devolverá la traza completa en Swagger
        error_detalle = traceback.format_exc()
        raise HTTPException(status_code=500, detail=f"Error inesperado: {str(e)} | Trace: {error_detalle}")