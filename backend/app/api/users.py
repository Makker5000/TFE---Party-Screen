from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm
from app.db import get_db
from app import models, utils
from app.models.user import UserCreate, LoginUser, UpdatePassword, UpdateUsername, User
from app.utils.usersAuth import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user
)

router = APIRouter(
)


# --- ROUTES ---
# ----------- Connexion --------------
@router.post("/login")
def login_user(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    OAuth2PasswordRequestForm attend les champs : 
      - username -> on l'utilise pour l'email
      - password -> mot de passe
    """
    # On considère que l'utilisateur passe son email dans le champ "username"
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user:
        raise HTTPException(status_code=401, detail="Identifiants invalides")

    if not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Identifiants invalides")

    access_token = create_access_token(data={"user_id": user.id})
    return {"access_token": access_token, "token_type": "bearer"}


# ---------- Inscription -----------
@router.post("/register", status_code=status.HTTP_201_CREATED)
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    # Vérifier si email ou username existe déjà
    exist_email = db.query(User).filter(User.email == user.email).first()
    if exist_email:
        raise HTTPException(status_code=400, detail="Email déjà utilisé")

    exist_username = db.query(User).filter(User.username == user.username).first()
    if exist_username:
        raise HTTPException(status_code=400, detail="Nom d'utilisateur déjà utilisé")

    hashed_pw = hash_password(user.password)
    new_user = User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_pw
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": "Compte créé avec succès", "user_id": new_user.id}


# -------------- Changer user -----------
@router.put("/username")
def update_username(payload: UpdateUsername, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Le current_user est injecté grâce à get_current_user() (dépendance)
    # Si le nouveau username existe déjà, on refuse
    check = db.query(User).filter(User.username == payload.new_username).first()
    if check:
        raise HTTPException(status_code=400, detail="Ce nom d'utilisateur est déjà pris")

    current_user.username = payload.new_username
    db.commit()
    return {"message": "Nom d'utilisateur mis à jour"}


# --------------- Changer password ---------------
@router.put("/password")
def update_password(payload: UpdatePassword, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not verify_password(payload.current_password, current_user.hashed_password):
        raise HTTPException(status_code=401, detail="Mot de passe actuel incorrect")

    current_user.hashed_password = hash_password(payload.new_password)
    db.commit()
    return {"message": "Mot de passe mis à jour"}


# -------------- Delete User / Account -------------
@router.delete("/delete", status_code=status.HTTP_200_OK)
def delete_user(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db.delete(current_user)
    db.commit()
    return {"message": "Compte supprimé"}


# ------------- Deconnexion --------------
@router.post("/logout")
def logout():
    # À adapter selon ta gestion d'auth (JWT, sessions, cookies, etc.)
    return {"message": "Déconnecté"}