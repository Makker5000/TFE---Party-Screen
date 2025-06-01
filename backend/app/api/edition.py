from fastapi import APIRouter, UploadFile, File, HTTPException
from app.models.edition import BrightnessModel, ArtistVisualModel, LyricsModel, AdsModel, QRCodeModel #, SongRequest
from app.utils.qrcode import create_qr_code, resize_qr_code, qr_to_raw_base64
from app.utils.mqtt import publish
from app.core.config import MQTT_TOPIC
import shutil, os, uuid
import json
import io, base64
import subprocess
from pathlib import Path
import sounddevice as sd
from scipy.io.wavfile import write
import requests
from dotenv import load_dotenv
import asyncio
import re
from typing import Union

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
# UPLOAD_DIR_VISUAL = "app/uploads/visuals"

# # S'assurer que le dossier existe
# os.makedirs(UPLOAD_DIR_VISUAL, exist_ok=True)

# @router.post("/visual/upload")
# async def upload_visual(file: UploadFile = File(...)):
#     # Vérifier le type de fichier accepté
#     allowed_types = ["image/jpeg", "image/png", "image/gif", "video/mp4"]
#     if file.content_type not in allowed_types:
#         raise HTTPException(status_code=400, detail="Type de fichier non supporté")

#     # Générer un nom unique
#     ext = os.path.splitext(file.filename)[1]
#     unique_filename = f"{uuid.uuid4()}{ext}"
#     file_path = os.path.join(UPLOAD_DIR_VISUAL, unique_filename)

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
UPLOAD_DIR_VISUAL = "app/uploads/visuals"

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
    file_path = os.path.join(UPLOAD_DIR_VISUAL, unique_filename)

    # 🔧 Redimensionner image si besoin
    if file.content_type.startswith("image"):
        img = Image.open(file.file).convert("RGB")
        resized_img = img.resize((width, height))
        resized_img.save(file_path, format="PNG")

        # 3) Convertir en RAW565
        pixels = resized_img.load()
        raw565 = bytearray()
        for y in range(height):
            for x in range(width):
                r, g, b = pixels[x, y]
                # convertir 8 bits → 5/6/5
                r5 = (r >> 3) & 0x1F
                g6 = (g >> 2) & 0x3F
                b5 = (b >> 3) & 0x1F
                rgb565 = (r5 << 11) | (g6 << 5) | b5
                # stocker en big endian (MSB puis LSB)
                raw565.append((rgb565 >> 8) & 0xFF)
                raw565.append(rgb565 & 0xFF)

        # 4) Encoder ce raw565 en Base64
        b64_data = base64.b64encode(bytes(raw565)).decode("utf-8")

        # 5) Sauvegarder la chaîne Base64 dans un fichier .b64 (même basename + ".b64")
        b64_filename = unique_filename + ".b64"
        b64_path = os.path.join(UPLOAD_DIR_VISUAL, b64_filename)
        with open(b64_path, "w") as f_b64:
            f_b64.write(b64_data)

    else:
        # Vidéos, gif → sauvegarde brut
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        # On met b64_data à None pour signaler qu’il n’y a pas de RAW565
        b64_data = None
        b64_filename = None

    return {
        "status": "Upload réussi",
        "filename": unique_filename,   # Renvoie au front pour la suite “Play”
        "width": width,
        "height": height,
        "has_raw565": b64_data is not None
    }
    

@router.post("/visual/play")
async def play_visual(req: ArtistVisualModel):
    """
    - Lit le fichier Base64 précédemment généré lors de l’upload (<filename>.b64).
    - Construit le payload MQTT : { "FLAG": "VISUAL_PLAY", "picture": "<base64_RAW565>" }.
    - Envoie tout ça sur le topic configuré.
    """
    unique_filename = req.media
    b64_filename    = unique_filename + ".b64"
    b64_path        = os.path.join(UPLOAD_DIR_VISUAL, b64_filename)

    # Vérifier que le fichier .b64 existe
    if not os.path.exists(b64_path):
        raise HTTPException(status_code=404, detail=f"Le fichier Base64 pour '{unique_filename}' n'existe pas.")

    # Charger la chaîne Base64
    with open(b64_path, "r") as f:
        b64_data = f.read().strip()

    # Construire le payload MQTT
    payload = {
        "FLAG": "VISUAL_PLAY",
        "picture": b64_data
    }

    publish(MQTT_TOPIC, str(payload))

    return {"status": "Play command envoyé", "filename": unique_filename}


@router.post("/visual/stop")
async def stop_visual():
    """
    - Envoie simplement { "FLAG": "VISUAL_STOP" } sur le broker MQTT.
    """
    payload = {
        "FLAG": "VISUAL_STOP"
    }

    publish(MQTT_TOPIC, str(payload))

    return {"status": "Stop command envoyé"}


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
UPLOAD_DIR_LYRICS = Path("./app/uploads/lyrics")
UPLOAD_DIR_LYRICS.mkdir(parents=True, exist_ok=True)

AUDIO_PATH = UPLOAD_DIR_LYRICS / "test.wav"

playing_lyrics: Union[asyncio.Task, None] = None

async def record_and_get_path(durée: int = 15) -> Path:
    # # Lance arecord pour 'durée' secondes /!\ --> UNIQUEMENT sous Linux !!! /!\
    # cmd = [
    #     "arecord",
    #     "-D", "plughw:1,0",        # adapte à ton device
    #     "-f", "cd",
    #     "-t", "wav",
    #     "-d", str(durée),
    #     str(AUDIO_PATH)
    # ]
    # subprocess.run(cmd, check=True)
    # return AUDIO_PATH

    sample_rate = 44100  # Qualité CD
    print(f"📢 Enregistrement audio de {durée} secondes...")
    audio = sd.rec(int(durée * sample_rate), samplerate=sample_rate, channels=2)
    sd.wait()  # Attend la fin de l'enregistrement
    write(str(AUDIO_PATH), sample_rate, audio)
    return AUDIO_PATH


def recognize_music_with_audd(file_path: str) -> dict:
    """
    Envoie un fichier audio à l'API AudD pour reconnaissance musicale.
    
    Args:
        file_path (str): Chemin vers le fichier audio.
        api_token (str): Clé API AudD.

    Returns:
        dict: Dictionnaire contenant l'artiste, le titre, ou une erreur.
    """
    url = "https://api.audd.io/"

    load_dotenv()  # lit ton .env

    api_token = os.getenv("AUDD_TOKEN")

    with open(file_path, 'rb') as audio_file:
        files = {
            'file': audio_file,
        }
        data = {
            'api_token': api_token,
            'return': 'apple_music,spotify',  # tu peux enlever si tu veux moins de données
        }

        response = requests.post(url, data=data, files=files)
    
    if response.status_code == 200:
        result = response.json()
        if result.get("status") == "success" and result.get("result"):
            title = result["result"].get("title")
            artist = result["result"].get("artist")
            return {"title": title, "artist": artist}
        else:
            return {"error": "Musique non reconnue."}
    else:
        return {"error": f"Erreur API: {response.status_code} - {response.text}"}
    

def get_lyrics(data: dict):
    title = data.get("title")
    artist = data.get("artist")

    if not title or not artist:
        raise HTTPException(status_code=400, detail="Title and artist are required")

    base_url = "https://api.lyrics.ovh/v1"
    url = f"{base_url}/{artist}/{title}"

    response = requests.get(url)

    if response.status_code == 200:
        lyrics_data = response.json()
        return {"lyrics": lyrics_data.get("lyrics", "No lyrics found.")}
    else:
        raise HTTPException(status_code=404, detail="Lyrics not found.")
    

async def play_lyrics_blocks(lyrics_data: dict, topic: str):
    lyrics = lyrics_data.get("lyrics", "")
    
    # Découpage des paroles en phrases (chaque ligne non vide ou bloc de texte)
    blocks = [line.strip() for line in re.split(r'\r?\n+', lyrics) if line.strip()]
    

    for i, block in enumerate(blocks, 1):
        payload = {
            "FLAG": "LYRICS_BLOCK",
            "index": i,
            "text": block
        }
        publish(topic, payload)
        print(f"Bloc {i} envoyé : {block}")
        await asyncio.sleep(3)

    # Message de fin
    publish(topic, {"FLAG": "LYRICS_STOP"})
    print("🎉 Tous les lyrics ont été envoyés !")


@router.post("/lyrics/play")
async def play_lyrics(data: LyricsModel):
    global playing_lyrics

    # Stoppe la tâche précédente si elle existe
    if playing_lyrics is not None and not playing_lyrics.done():
        playing_lyrics.cancel()
        try:
            await playing_lyrics
        except asyncio.CancelledError:
            print("Ancienne tâche annulée")

    payload = { "FLAG": "LYRICS_PLAY", **data.dict() }
    publish(MQTT_TOPIC, payload)

    # Enregistrement Audio de 5sec pour l'envoyer à API Reconnaissance Musicale
    # audio_file = await record_and_get_path(durée=10)
    # if audio_file != 0:
    #     print("Fichier Audio créer et enregistré !")

    # Envoyer le Son à l'API AudD et récupérer Titre + Artiste
    # meta_data = recognize_music_with_audd(audio_file)
    # print(f"Titre et Artiste reconnu par AudD : {meta_data}")

    # chanson1 = {'title': "La vie qu'on mène", 'artist': 'Ninho'}

    # Récupération des Paroles de la chanson détectée
    # lyrics_data = get_lyrics(meta_data)
    lyrics_data = {'lyrics': "No me importa lo que de mí se diga\r\nVida usted su vida, que yo vivo la mia\r\nQue solo es una, disfruta el momento\r\nQue el tiempo se acaba y pa'trás no vira\r\nBebiendo, fumando y jodiendo\n\nSigo vacilando de party to' los día'\n\nSíguelo, oh-oh-oh, oh-oh-oh, oh-oh (¡Farru!)\n\nSíguelo, oh-oh-oh, oh-oh-oh, oh-oh (La rola y pepa)\n\n\n\nPepa y agua pa' la seca\n\nTo' el mundo en pastilla en la discoteca\n\nPepa y agua pa' la seca\n\nTo' el mundo en pastilla en la discoteca\n\n\n\nDesacata'o\n\nEmpastilla'o\n\n(Qué maldita nota)\n\n(Arcoíris)\n\n¡Fa-Farru!\n\n\n\n"}
    print(f"Les Lyrics du son capté : {lyrics_data}")

    # Découpage et envoie des Paroles par blocs via MQTT
    playing_lyrics = asyncio.create_task(play_lyrics_blocks(lyrics_data, MQTT_TOPIC))

    return {"status": "ok"}

@router.post("/lyrics/stop")
async def stop_lyrics():
    global playing_lyrics

    if playing_lyrics is not None and not playing_lyrics.done():
        playing_lyrics.cancel()
        try:
            await playing_lyrics
        except asyncio.CancelledError:
            print("Tâche lyrics annulée")

    publish(MQTT_TOPIC, { "FLAG": "LYRICS_STOP" })
    return {"status": "ok"}


# ############################################# FIN Lyrics ##################################################
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
