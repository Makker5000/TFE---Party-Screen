from fastapi import APIRouter
from app.models.settings import PowerModel, SettingsModel
from app.utils.mqtt import publish
from app.core.config import MQTT_TOPIC

import os, json

router = APIRouter()

current_power: bool = 'true';

@router.post("/power")
async def set_power(data: PowerModel):
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
async def get_power():
    """
    Renvoie la dernière valeur de l'état Power.
    """
    print(f"Power state : {current_power}")
    return {"power": current_power}

# @router.post("/config")
# async def apply_settings(data: SettingsModel):
#     payload = {
#         "flag": "CONFIG",
#         "screenCount": data.screenCount,
#         "matrixCount": data.matrixCount,
#         "screenShape": data.screenShape
#     }
#     publish(MQTT_TOPIC, payload)
#     return {"status": "ok", "sent": payload}

SETTINGS_PATH = "app/data/settings.json"
os.makedirs("app/data", exist_ok=True)

@router.post("/config")
async def apply_settings(data: SettingsModel):
    payload = {
        "FLAG": "CONFIG",
        "screenCount": data.screenCount,
        "matrixCount": data.matrixCount,
        "screenShape": data.screenShape
    }

    # 💾 Sauvegarde les paramètres en local
    with open(SETTINGS_PATH, "w") as f:
        json.dump(payload, f)

    publish(MQTT_TOPIC, payload)
    return {"status": "ok", "sent": payload}

@router.get("/config")
async def get_current_settings():
    if os.path.exists(SETTINGS_PATH):
        with open(SETTINGS_PATH, "r") as f:
            data = json.load(f)
        return data
    return {
        "screenCount": 1,
        "matrixCount": 4,
        "screenShape": "Square"
    }