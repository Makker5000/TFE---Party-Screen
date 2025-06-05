from fastapi import APIRouter, Depends, HTTPException, status
from app.models.settings import PowerModel, SettingsModel, SettingsDB
from app.utils.mqtt import publish
from app.core.config import MQTT_TOPIC
from sqlalchemy.orm import Session
from app.db import get_db
from app.utils.usersAuth import get_current_user


import os, json

router = APIRouter()

current_power: bool = 'false';

@router.post("/power")
async def set_power(data: PowerModel, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    global current_power 
    current_power = data.power

    if current_power == True :
        payload = { 
            "FLAG": "POWER_ON",
        }
    elif current_power == False :
        payload = { 
            "FLAG": "POWER_OFF",
        }

    publish(MQTT_TOPIC, payload)
    return {"status": "ok", "sent": payload}

@router.get("/power")
async def get_power(current_user = Depends(get_current_user)):
    """
    Renvoie la dernière valeur de l'état Power.
    """
    print(f"Power state : {current_power}")
    return {"power": current_power}


SETTINGS_PATH = "app/data/settings.json"
os.makedirs("app/data", exist_ok=True)

@router.post("/config")
async def apply_settings(data: SettingsModel, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    # 1) On cherche si il n'exista pas déjà des settings pour ce user_id
    settings_db = (
        db.query(SettingsDB)
        .filter(SettingsDB.user_id == current_user.id)
        .first()
    )

    if not settings_db:
        # Création
        settings_db = SettingsDB(
            user_id=current_user.id,
            screen_count=data.screenCount,
            matrix_count=data.matrixCount,
            screen_shape=data.screenShape
        )
        db.add(settings_db)
    else:
        # Mise à jour
        settings_db.screen_count = data.screenCount
        settings_db.matrix_count = data.matrixCount
        settings_db.screen_shape = data.screenShape

    db.commit()
    # On n'oublie pas de rafraîchir l'objet si besoin : 
    # db.refresh(settings_db)

    # 2) Préparer le Payload pour l'envoie en MQTT
    payload = {
        "FLAG": "CONFIG",
        "screenCount": data.screenCount,
        "matrixCount": data.matrixCount,
        "screenShape": data.screenShape
    }

    publish(MQTT_TOPIC, payload)
    return {"status": "ok", "sent": payload}

@router.get("/config")
async def get_current_settings(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    # if os.path.exists(SETTINGS_PATH):
    #     with open(SETTINGS_PATH, "r") as f:
    #         data = json.load(f)
    #     return data
    # return {
    #     "screenCount": 1,
    #     "matrixCount": 4,
    #     "screenShape": "Square"
    # }

    settings_db = (
        db.query(SettingsDB)
        .filter(SettingsDB.user_id == current_user.id)
        .first()
    )

    if settings_db:
        return {
            "screenCount": settings_db.screen_count,
            "matrixCount": settings_db.matrix_count,
            "screenShape": settings_db.screen_shape,
        }

    # Valeurs par défaut si l'utilisateur n'a jamais sauvegardé
    return {
        "screenCount": 1,
        "matrixCount": 4,
        "screenShape": "Square"
    }