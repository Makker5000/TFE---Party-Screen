from passlib.context import CryptContext
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.db import get_db
from app import models
from app.models.user import User
import os
from datetime import timedelta, datetime
from typing import Optional

SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24

# --- 1) Hash du mot de passe ---
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

# --- 2) OAuth2 scheme ---
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/users/login")  # à ajuster plus tard
# → tokenUrl doit correspondre à la route d’authentification (endpoint /login)

# def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
#     # Tu mettras plus tard le décodage de ton JWT ici
#     user = db.query(models.users).filter(models.users.id == 1).first()  # temporaire
#     if not user:
#         raise HTTPException(status_code=401, detail="Utilisateur non trouvé")
#     return user

# --- 3) Création et décodage de JWT ---
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Génère un JWT encodé avec payload=data et expiration.  
    data doit contenir au minimum {"user_id": <int>}.
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> dict:
    """
    Décode le JWT et renvoie le payload s’il est valide, sinon lève une exception.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalide ou expiré",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
# --- 4) Récupérer l’utilisateur courant à partir du token ---
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    """
    Cette dépendance sera injectée dans les routes où l’on a besoin de savoir qui est connecté.  
    Elle décode le token, extrait user_id, et récupère l’objet User en BDD.  
    """
    payload = decode_access_token(token)
    user_id: int = payload.get("user_id")
    if user_id is None:
        raise HTTPException(status_code=401, detail="Token invalide : user_id manquant")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    return user

