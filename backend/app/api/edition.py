from fastapi import APIRouter, UploadFile, File, HTTPException
from app.models.edition import BrightnessModel, ArtistVisualModel, LyricsModel, AdsModel, QRCodeModel
from app.utils.qrcode import create_qr_code, resize_qr_code, qr_to_raw_base64
from app.utils.mqtt import publish
from app.core.config import MQTT_TOPIC
import shutil, os, uuid
import json
import io, base64

from PIL import Image
import json

router = APIRouter()

# ----------------- BRIGTHNESS ------------------
# Stockage en mémoire de la dernière valeur reçue
_current_brightness: int = 0

@router.post("/brightness")
async def set_brightness(data: BrightnessModel):
    global _current_brightness
    _current_brightness = data.brightness

    payload = {
        "FLAG": "BRIGHTNESS",
        "value": data.brightness
    }
    publish(MQTT_TOPIC, payload)
    return {"status": "ok", "sent": payload}

@router.get("/brightness")
async def get_brightness():
    """
    Renvoie la dernière valeur de luminosité réglée.
    """
    return {"brightness": _current_brightness}

# --------------- ARTIST VISUALS ----------------
# @router.post("/visual/play")
# async def display_artist_visuals(data: ArtistVisualModel):
#     payload = {
#         "FLAG": "ARTIST_VISUALS_PLAY",
#         "media": data.media
#     }
#     publish(MQTT_TOPIC, payload)
#     return {"status": "ok", "sent": payload}

# @router.post("/visual/stop")
# async def display_artist_visuals(data: ArtistVisualModel):
#     payload = {
#         "FLAG": "ARTIST_VISUALS_STOP",
#     }
#     publish(MQTT_TOPIC, payload)
#     return {"status": "ok", "sent": payload}

################### Fonctionne mais pas Complet ! ############################
# UPLOAD_DIR = "app/uploads/visuals"

# # S'assurer que le dossier existe
# os.makedirs(UPLOAD_DIR, exist_ok=True)

# @router.post("/visual/upload")
# async def upload_visual(file: UploadFile = File(...)):
#     # Vérifier le type de fichier accepté
#     allowed_types = ["image/jpeg", "image/png", "image/gif", "video/mp4"]
#     if file.content_type not in allowed_types:
#         raise HTTPException(status_code=400, detail="Type de fichier non supporté")

#     # Générer un nom unique
#     ext = os.path.splitext(file.filename)[1]
#     unique_filename = f"{uuid.uuid4()}{ext}"
#     file_path = os.path.join(UPLOAD_DIR, unique_filename)

#     # Sauvegarder le fichier
#     with open(file_path, "wb") as buffer:
#         shutil.copyfileobj(file.file, buffer)

#     # Préparer le chemin public (ou celui que le ESP peut utiliser)
#     file_url = f"http://localhost:8000/app/uploads/visuals/{unique_filename}"
#     # file_url = f"http://localhost:8000/static/visuals/{unique_filename}"

#     # Publier sur MQTT
#     payload = {
#         "flag": "ARTIST_VISUAL",
#         "file_url": file_url
#     }
#     publish(MQTT_TOPIC, str(payload))

#     return {
#         "status": "Fichier uploadé et notifié",
#         "file_url": file_url
#     }
######################## Fonctionnel avec redimensionnement d'image ! ################################

SETTINGS_PATH = "app/data/settings.json"
UPLOAD_DIR = "app/uploads/visuals"

def load_settings():
    if os.path.exists(SETTINGS_PATH):
        with open(SETTINGS_PATH, "r") as f:
            return json.load(f)
    return {
        "screenCount": 1,
        "matrixCount": 4,
        "screenShape": "square"
    }

@router.post("/visual/upload")
async def upload_visual(file: UploadFile = File(...)):
    settings = load_settings()
    matrix_count = settings["matrixCount"]
    screen_count = settings["screenCount"]
    shape = settings["screenShape"]

    # ✅ Vérif : minimum 4 matrices et 1 écran
    if matrix_count < 4 or screen_count < 1:
        raise HTTPException(status_code=400, detail="Configuration invalide : minimum 4 matrices et 1 écran requis.")

    # ✅ Déduire résolution globale
    if shape == "square":
        width = height = int((matrix_count * 16) ** 0.5)
    else:  # suppose un écran horizontal
        width = matrix_count * 16
        height = 16 * screen_count

    # Vérifier type
    allowed_types = ["image/jpeg", "image/png", "image/gif", "video/mp4"]
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Type de fichier non supporté")

    # Nom unique
    ext = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid.uuid4()}{ext}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)

    # 🔧 Redimensionner image si besoin
    if file.content_type.startswith("image"):
        img = Image.open(file.file)
        resized_img = img.resize((width, height))
        resized_img.save(file_path)
    else:
        # Vidéos, gif → sauvegarde brut
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

    file_url = f"http://localhost:8000/static/visuals/{unique_filename}"
    payload = {
        "FLAG": "ARTIST_VISUAL",
        "file_url": file_url
    }
    publish(MQTT_TOPIC, str(payload))

    return {
        "status": "Fichier uploadé et adapté à l'écran",
        "resolution": f"{width}x{height}",
        "file_url": file_url
    }

########################################################


# --------------- QRCODE ----------------
# @router.post("/qrcode")
# async def generate_qrcode(data: QRCodeModel):
#     # TODO : Faire en sorte qu'il récupère le lien avec 'data.url' et puis il génère un QR Code qu'il envoie ensuite à l'ESP Père.
#     """
#     qr_code_bin = createQR(data.url)
#     payload = {
#         "FLAG": "QRCODE_GENERATE",
#         "data": qr_code_bin,
#     }
#     """
#     return None

# @router.post("/qrcode/play")
# async def play_qrcode(data: QRCodeModel):
#     if data.url == "play":
#         publish(MQTT_TOPIC, { "FLAG": "QRCODE_PLAY"})
#     else:
#         return "Erreur ce n'est pas le FLAG attendu !"
#     return {"status": "ok"}

# @router.post("/qrcode/stop")
# async def stop_qrcode(data: QRCodeModel):
#     if data.url == "stop":
#         publish(MQTT_TOPIC, { "FLAG": "QRCODE_STOP"})
#     else:
#         return "Erreur ce n'est pas le FLAG attendu !"
#     return {"status": "ok"}

###################### Fonctionnel avec redimensionnement (Tester affichage QR Code et si mène bien à la Page ###############################
# DEFAULT_URL = "http://localhost:5173/lyrics"

# @router.post("/qrcode")
# async def generate_qrcode(data: QRCodeModel):
#     # Étape 1 : Récupération de l'URL
#     url = data.url if data.url else DEFAULT_URL

#     # Étape 2 : Génération QR brut
#     qr_code_bin = create_qr_code(url)

#     # Étape 3 : Lecture de la config écran (fichier JSON temporaire)
#     if os.path.exists(SETTINGS_PATH):
#         with open(SETTINGS_PATH, "r") as f:
#             settings = json.load(f)
#     else:
#         settings = {
#             "screenCount": 1,
#             "matrixCount": 9,
#             "screenShape": "square"
#         }

#     screen_count = settings.get("screenCount", 1)
#     matrix_count = settings.get("matrixCount", 9)
#     screen_shape = settings.get("screenShape", "square")

#     # Étape 4 : Redimensionnement du QR code
#     resized_qr = resize_qr_code(qr_code_bin, screen_count, matrix_count, screen_shape)

#    # Étape 5 : Envoi à l’ESP
#    # payload = {
#    #     "FLAG": "QRCODE_GENERATE",
#    #     "data": resized_qr,
#    # }
#    # publish(MQTT_TOPIC, payload)
#
#     return {"status": "QR Code generated and sent"}
# --------------------- ///////////////////////////////////////////// -------------------
# DEFAULT_URL = "http://localhost:5173/lyrics"

# @router.post("/qrcode")
# async def generate_qrcode(data: QRCodeModel):
#     # 1) Génération QR PIL.Image
#     url = data.url or DEFAULT_URL
#     qr_img = create_qr_code(url)

#     # 2) Charger config écran
#     if os.path.exists(SETTINGS_PATH):
#         settings = json.load(open(SETTINGS_PATH))
#     else:
#         settings = {"screenCount":1, "matrixCount":9, "screenShape":"square"}

#     # 3) Redimensionner vers une PIL.Image finale
#     resized_img = resize_qr_code(qr_img,
#                                   settings["screenCount"],
#                                   settings["matrixCount"],
#                                   settings["screenShape"])

#     # 4) Conversion en raw RGB888 base64
#     width, height, raw_b64 = qr_to_raw_base64(resized_img)

#     # 5) Publication MQTT
#     payload = {
#         "FLAG": "DISPLAY_RAW",
#         "width": width,
#         "height": height,
#         "data": raw_b64
#     }
#     publish(MQTT_TOPIC, payload)

#     return {"status": "QR Code generated and sent"}

DEFAULT_URL = "http://localhost:5173/lyrics"

@router.post("/qrcode")
async def generate_qrcode(data: QRCodeModel):
    # 1) Génération QR PIL.Image
    url = data.url or DEFAULT_URL
    qr_img = create_qr_code(url)

    # 2) Charger config écran
    if os.path.exists(SETTINGS_PATH):
        settings = json.load(open(SETTINGS_PATH))
    else:
        settings = {"screenCount":1, "matrixCount":9, "screenShape":"square"}

    # 3) Redimensionner vers une PIL.Image finale
    resized_img = resize_qr_code(qr_img,
                                  settings["screenCount"],
                                  settings["matrixCount"],
                                  settings["screenShape"])

    # 4) Conversion en raw RGB888 base64
    width, height, raw_b64 = qr_to_raw_base64(resized_img)

    # 5) Publication MQTT
    payload = {
        "FLAG": "DISPLAY_QR",
        "width": width,
        "height": height,
        "data": raw_b64,
        "qr_content": url,
    }
    publish(MQTT_TOPIC, payload)

    # 6) NOUVEAU: Conversion pour le frontend (base64 standard)
    # Convertir PIL Image en base64 PNG pour l'affichage web
    buffer = io.BytesIO()
    resized_img.save(buffer, format='PNG')
    img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    
    return {
        "status": "QR Code generated and sent",
        "image": f"data:image/png;base64,{img_base64}",
        "width": width,
        "height": height
    }


###############################################################

# --------------- LYRICS ---------------- ############### (A IMPLEMENTER !!!) #####################
@router.post("/lyrics/play")
async def play_lyrics(data: LyricsModel):
    payload = { "FLAG": "LYRICS_PLAY", **data.dict() }
    publish(MQTT_TOPIC, payload)
    return {"status": "ok"}

@router.post("/lyrics/stop")
async def stop_lyrics():
    publish(MQTT_TOPIC, { "FLAG": "LYRICS_STOP" })
    return {"status": "ok"}

# --------------- ADS ----------------
@router.post("/ads/play")
async def play_ads(data: AdsModel):
    if data.state == "play":
        print(f"Contenu du message : {data.content}")
        payload = { "FLAG": "ADS_PLAY", **data.dict() } # Faire en sorte d'exclure la balise 'state' !
        publish(MQTT_TOPIC, payload)
    else:
        return "Pas le bon état pour PLAY !"
    return {"status": "ok"}

@router.post("/ads/stop")
async def stop_ads(data: AdsModel):
    if data.state == "stop":
        print(f"Arrêt de l'affichage du message : {data.content} !!")
        publish(MQTT_TOPIC, { "FLAG": "ADS_STOP" })
    else:
        print("Erreur lors de la condition ! Pas le bon état pour STOP !")
    return {"status": "ok"}
