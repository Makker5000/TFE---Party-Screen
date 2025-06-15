import hashlib
import hmac
import time
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, status
from shazamio import Shazam
from app.models.edition import BrightnessModel, ArtistVisualModel, LyricsModel, AdsModel, QRCodeModel, QRCodePlayModel, ArtistVisualDB, QrcodeDB
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
import math

from PIL import Image
import json

from sqlalchemy.orm import Session
from app.db import get_db
from app.utils.usersAuth import get_current_user
from app.models.settings import SettingsDB
from app.utils.normalize_accents import strip_accents

router = APIRouter()

# ####################################### BRIGTHNESS #######################################
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


# ################################ ARTIST VISUALS ################################
UPLOAD_DIR_VISUAL = "app/uploads/visuals"
ALLOWED_IMAGE_TYPES = ["image/jpeg", "image/png", "image/gif"]
ALLOWED_VIDEO_TYPES = ["video/mp4"]

@router.post("/visual/upload")
async def upload_visual(file: UploadFile = File(...), db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    """
    1. On récupère la ligne 'settings' en base pour l'utilisateur.
    2. On vérifie que (screen_count, matrix_count, screen_shape) est l'une des 4 combinaisons autorisées :
       - (1, 4, "Square")
       - (1, 9, "Square")
       - (1, 6, "Horizontal Rectangle")
       - (1, 6, "Vertical Rectangle")
       Sinon on renvoie HTTPException(400).
    3. On calcule width/height en fonction de cette config, on redimensionne si image, on stocke, etc.
    """

    # ──── 1) Récupération des settings depuis la table en base ────
    settings_row = (
        db.query(SettingsDB)
        .filter(SettingsDB.user_id == current_user.id)
        .first()
    )

    if settings_row is None:
        # Si jamais l’utilisateur n’a pas enregistré de settings, on peut choisir des valeurs par défaut
        screen_count = 1
        matrix_count = 4
        shape = "Square"
    else:
        screen_count = int(settings_row.screen_count)
        matrix_count = int(settings_row.matrix_count)
        shape = settings_row.screen_shape

    # ──── 2) Vérification des combinaisons autorisées ────
    # On calcule un tuple pour simplifier la comparaison
    combo = (screen_count, matrix_count, shape)

    valid_combos = [
        (1, 4, "Square"),
        (1, 9, "Square"),
        (1, 6, "Horizontal Rectangle"),
        (1, 6, "Vertical Rectangle"),
    ]

    if combo not in valid_combos:
        # Le détail du message peut être personnalisé :
        raise HTTPException(
            status_code=400,
            detail=(
                "Configuration invalide : les paramètres actuels ("
                f"screenCount={screen_count}, matrixCount={matrix_count}, screenShape='{shape}') "
                "doivent être l’une de ces combinaisons :\n"
                "• (1, 4, 'Square')\n"
                "• (1, 9, 'Square')\n"
                "• (1, 6, 'Horizontal Rectangle')\n"
                "• (1, 6, 'Vertical Rectangle')"
            )
        )

    # ──── 3) On calcule width/height en fonction du shape et matrix_count ────
    if shape == "Square":
        # On s'assure que matrix_count est un carré parfait
        side_matrices = int(math.isqrt(matrix_count))
        if side_matrices * side_matrices != matrix_count:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Pour shape='Square', matrixCount={matrix_count} doit être un carré parfait "
                    "(exemple : 4, 9, 16, …)."
                )
            )
        width = int(side_matrices * 16)
        height = int(side_matrices * 16)

    elif shape == "Horizontal Rectangle":
        # Pour « Horizontal Rectangle » ou « Vertical Rectangle »
        # largeur = nombre de matrices horizontales × 16
        # hauteur = nombre de matrices verticales × 16  (screen_count vaut 1 ici)
        width = int((6 / 2) * 16)
        height = int((6 / 3) * 16)

    elif shape == "Vertical Rectangle":
        # Pour « Horizontal Rectangle » ou « Vertical Rectangle »
        # largeur = nombre de matrices horizontales × 16
        # hauteur = nombre de matrices verticales × 16  (screen_count vaut 1 ici)
        width = int((6 / 3) * 16)
        height = int((6 / 2) * 16)
    
    else : 
        # On s'assure que matrix_count est un carré parfait
        side_matrices = int(math.isqrt(matrix_count))
        if side_matrices * side_matrices != matrix_count:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Pour shape='Square', matrixCount={matrix_count} doit être un carré parfait "
                    "(exemple : 4, 9, 16, …)."
                )
            )
        width = int(side_matrices * 16)
        height = int(side_matrices * 16)


     # ─── 4) Vérification du type de fichier ───
    content_type = file.content_type or ""
    is_image = content_type.startswith("image/")
    is_video = content_type.startswith("video/")

    if is_image and content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(status_code=400, detail="Type d'image non supporté.")
    if is_video and content_type not in ALLOWED_VIDEO_TYPES:
        raise HTTPException(status_code=400, detail="Type de vidéo non supporté.")

    # Génération d'un nom unique (UUID + extension)
    ext = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid.uuid4()}{ext}"

    if is_image:
        # ─── 4.a) On redimensionne l'image en PIL ───
        img = Image.open(file.file).convert("RGB")
        resized_img = img.resize((width, height))

        # ─── 4.b) Génération du raw888 → base64 ───
        pixels = resized_img.load()
        raw888 = bytearray()
        for y in range(height):
            for x in range(width):
                r, g, b = pixels[x, y]
                raw888.extend([r, g, b])

        b64_data = base64.b64encode(bytes(raw888)).decode("utf-8")

        # ─── 4.c) Insertion dans la table `visuals` ───
        new_visual = ArtistVisualDB(
            filename=unique_filename,
            data_base64=b64_data
        )
        db.add(new_visual)
        db.commit()
        db.refresh(new_visual)  # pour récupérer new_visual.id

        # ──── 6) Réponse JSON  ────
        return {
            "status": "Upload réussi",
            "id": new_visual.id,
            "filename": unique_filename,
            "width": width,
            "height": height,
            "is_image": True
        }
    
    else :
        # ─── 4.d) POUR LES VIDÉOS (optionnel) ───
        # On sauvegarde toujours dans un dossier pour les vidéos (pas de base64)
        os.makedirs(UPLOAD_DIR_VISUAL, exist_ok=True)
        file_path = os.path.join(UPLOAD_DIR_VISUAL, unique_filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        return {
            "status": "Upload réussi",
            "id": None,
            "filename": unique_filename,
            "width": width,
            "height": height,
            "is_image": False
        }


@router.post("/visual/play")
async def play_visual(req: dict, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    """
    On s’attend à recevoir JSON : { "media": "<filename>" }
    Pour les images, on va rechercher le base64 en DB via le filename.
    """
    filename = req.get("media")
    if not filename:
        raise HTTPException(status_code=400, detail="Le champ 'media' est requis.")

    # ─── 1) On cherche dans la table `visuals` le base64 associé
    visual_row = db.query(ArtistVisualDB).filter(ArtistVisualDB.filename == filename).first()
    if not visual_row:
        raise HTTPException(
            status_code=404,
            detail=f"Aucune image en base pour le filename '{filename}'."
        )

    # ─── 2) On construit le payload MQTT pour l’image
    payload = {
        "FLAG": "VISUAL_PLAY",
        "width": 48,
        "height": 48,
        "picture": visual_row.data_base64
    }
    publish(MQTT_TOPIC, payload)

    return {"status": "Play command envoyé", "filename": filename}


@router.post("/visual/stop")
async def stop_visual(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    """
    Envoie simplement {"FLAG": "VISUAL_STOP"} sur le broker MQTT.
    """
    payload = { "FLAG": "VISUAL_STOP" }
    publish(MQTT_TOPIC, payload)
    return {"status": "Stop command envoyé"}


# ################################### QRCODE ####################################
DEFAULT_URL = "https://tfe-twampi.vercel.app/"
UPLOAD_DIR_QRCODE = "app/uploads/qrcodes"
os.makedirs(UPLOAD_DIR_QRCODE, exist_ok=True)

@router.post("/qrcode", status_code=status.HTTP_200_OK)
async def generate_qrcode(data: QRCodeModel, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    # 1) On va chercher la config de l'écran et on Vérifie les conditions 
    settings_row = db.query(SettingsDB).order_by(SettingsDB.id.desc()).first()
    # S'il n'y a pas de ligne settings, on considère les valeurs par défaut (1,9,"Square")
    if not settings_row:
        screen_count, matrix_count, screen_shape = 1, 9, "Square"
    else:
        screen_count = int(settings_row.screen_count)
        matrix_count = int(settings_row.matrix_count)
        screen_shape = settings_row.screen_shape

    # Vérification stricte de la combinaison autorisée
    if not (screen_count == 1 and matrix_count == 9 and screen_shape == "Square"):
        raise HTTPException(
            status_code=400,
            detail=(
                "Configuration invalide pour QR Code : "
                f"(screenCount={screen_count}, matrixCount={matrix_count}, screenShape='{screen_shape}'). "
                "Seule la configuration (1, 9, 'Square') est autorisée."
            )
        )

    # 2) Génération QR PIL.Image
    url = data.url or DEFAULT_URL
    qr_img = create_qr_code(url)


    # 4) Redimensionner vers une PIL.Image finale 48x48
    resized_img = resize_qr_code(qr_img)

    # 5) Conversion en raw RGB888 base64
    width, height, raw_b64 = qr_to_raw_base64(resized_img)

    # Chercher s'il existe déjà en DB pour ce user+URL
    existing = (
        db.query(QrcodeDB)
        .filter(QrcodeDB.user_id == current_user.id, QrcodeDB.url == url)
        .first()
    )

    if existing:
        # on met juste à jour data_base64
        existing.data_base64 = raw_b64
        db.commit()
        qrcode_id = existing.id
    else:
        # on crée un nouveau record
        new_qr = QrcodeDB(
            user_id=current_user.id,
            url=url,
            data_base64=raw_b64,
            preset_id=None
        )
        db.add(new_qr)
        db.commit()
        db.refresh(new_qr)
        qrcode_id = new_qr.id

    # # 5bis) On génère un nom de fichier unique et puis on sauvegarde
    # filename_base = str(uuid.uuid4())
    # png_path = os.path.join(UPLOAD_DIR_QRCODE, f"{filename_base}.png")
    # b64_path = os.path.join(UPLOAD_DIR_QRCODE, f"{filename_base}.txt")

    # # 5.a) Sauvegarder l'image PNG (pour affichage éventuel)
    # resized_img.save(png_path, format="PNG")
    # # 5.b) Sauvegarder la chaîne raw888 Base64 dans .txt
    # with open(b64_path, "w", encoding="utf-8") as f_txt:
    #     f_txt.write(raw_b64)

    # 7) NOUVEAU: Conversion pour le frontend (base64 standard)
    # Convertir PIL Image en base64 PNG pour l'affichage web
    buffer = io.BytesIO()
    resized_img.save(buffer, format='PNG')
    img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    
    return {
        "status": "QR Code generated and sent",
        "id": qrcode_id,
        "image": f"data:image/png;base64,{img_base64}",
        "width": width,
        "height": height,
        "url": url
    }


@router.post("/qrcode/play", status_code=status.HTTP_200_OK)
async def play_qrcode(data: QRCodePlayModel, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    
    # 1) Lecture des settings (on valide la même condition)
    settings_row = db.query(SettingsDB).order_by(SettingsDB.id.desc()).first()
    if not settings_row:
        sc, mc, shape = 1, 9, "Square"
    else:
        sc = int(settings_row.screen_count)
        mc = int(settings_row.matrix_count)
        shape = settings_row.screen_shape
    if not (sc == 1 and mc == 9 and shape == "Square"):
        raise HTTPException(
            status_code=400,
            detail=(
                f"Config invalide (screenCount={sc}, matrixCount={mc}, screenShape='{shape}'). "
                "Seule (1,9,'Square') autorisée."
            )
        )
    
    qr_row = None
    url = None
    raw_b64 = None

    # 2) Si on reçoit un ID
    if data.id is not None:
        qr_row = db.query(QrcodeDB).filter(QrcodeDB.id == data.id, QrcodeDB.user_id == current_user.id).first()
        if not qr_row:
            raise HTTPException(status_code=404, detail="Qrcode not found")
        raw_b64 = qr_row.data_base64
        url = qr_row.url

    # 3) Sinon si on reçoit une URL
    elif data.url:
        url = data.url
        # Chercher en DB si déjà existant
        qr_row = (
            db.query(QrcodeDB)
            .filter(QrcodeDB.user_id == current_user.id, QrcodeDB.url == url)
            .first()
        )
        if qr_row:
            raw_b64 = qr_row.data_base64
        else:
            # on génère en mémoire sans PNG, direct raw888
            qr_img = create_qr_code(url)
            resized_img = resize_qr_code(qr_img)
            _, _, raw_b64 = qr_to_raw_base64(resized_img)

            # Créer le record en DB
            new_qr = QrcodeDB(
                user_id=current_user.id,
                url=url,
                data_base64=raw_b64,
                preset_id=None
            )
            db.add(new_qr)
            db.commit()
            db.refresh(new_qr)
            qr_row = new_qr

    else:
        raise HTTPException(status_code=422, detail="Il faut fournir `id` ou `url`.")

    # 4) Si l’appel vient d’un preset (dans data.url on pourrait avoir preset_id),
    #    on met à jour preset_id de ce QR. Mais la page Preset envoie seulement { url }, donc :
    #    on peut lier simplement le dernier preset de l’utilisateur si utile, ou laisser preset_id à None.
    #    Vous pouvez adapter ici pour lier au preset qui a lancé l’appel.

    # 5) Enfin, on publie sur MQTT
    payload = {
        "FLAG": "QR_PLAY",
        "width": 48,
        "height": 48,
        "data": raw_b64,
        "qr_content": url
    }
    publish(MQTT_TOPIC, payload)

    return {"status": "QR Code played", "id": qr_row.id, "url": url}


@router.post("/qrcode/stop", status_code=status.HTTP_200_OK)
async def stop_qrcode(data: QRCodePlayModel, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    
    if data.id is not None:
        qr_row = db.query(QrcodeDB).filter(QrcodeDB.id == data.id, QrcodeDB.user_id == current_user.id).first()
        if not qr_row:
            raise HTTPException(status_code=404, detail="Qrcode not found")

        # 1) Supprimer de la BD
        db.delete(qr_row)
        db.commit()
    elif data.url:
        qr_row = db.query(QrcodeDB) \
                   .filter(QrcodeDB.user_id==current_user.id, QrcodeDB.url==data.url) \
                   .first()
        if qr_row:
            db.delete(qr_row)
            db.commit()

    # 2) Publier le FLAG stop
    payload = {"FLAG": "QR_STOP"}
    publish(MQTT_TOPIC, payload)

    return {"status": "QR Code stopped and deleted", "id": data.id}



# ######################################## LYRICS ############################################
UPLOAD_DIR_LYRICS = Path("./app/uploads/lyrics")
UPLOAD_DIR_LYRICS.mkdir(parents=True, exist_ok=True)

AUDIO_PATH = UPLOAD_DIR_LYRICS / "test.wav"

playing_lyrics: Union[asyncio.Task, None] = None

async def record_and_get_path(durée: int = 4) -> Path:
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

    sample_rate = 22050  # Qualité CD
    print(f"📢 Enregistrement audio de {durée} secondes...")
    audio = sd.rec(int(durée * sample_rate), samplerate=sample_rate, channels=2)
    sd.wait()  # Attend la fin de l'enregistrement
    write(str(AUDIO_PATH), sample_rate, audio)
    return AUDIO_PATH

# ////////////////////////// Reconnaissance avec AudD (Trial Free expired (5$/month)) //////////////////////////
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

# ////////////////////// Reconnaissance avec ACRCloud (Ne Fonctionne PAS !!) ///////////////////////
# def recognize_music_with_acrcloud(file_path: str) -> dict:
#     """
#     Envoie un fichier audio à l'API ACRCloud pour reconnaissance musicale.

#     Args:
#         file_path (str): Chemin vers le fichier audio.

#     Returns:
#         dict: Dictionnaire contenant l'artiste, le titre, ou une erreur.
#     """
#     load_dotenv()

#     host = os.getenv("ACR_HOST")
#     access_key = os.getenv("ACR_ACCESS_KEY")
#     access_secret = os.getenv("ACR_ACCESS_SECRET")
#     endpoint = "/v1/identify"
#     url = f"https://{host}{endpoint}"

#     print("HOST   :", host)
#     print("URL    :", url)

#     http_method = "POST"
#     http_uri = endpoint
#     data_type = "audio"
#     signature_version = "1"
#     timestamp = str(int(time.time()))

#     string_to_sign = "\n".join([http_method, http_uri, access_key, data_type, signature_version, timestamp])
#     sign = base64.b64encode(
#         hmac.new(access_secret.encode('ascii'), string_to_sign.encode('ascii'), digestmod=hashlib.sha1).digest()
#     ).decode('ascii')

#     # with open(file_path, 'rb') as f:
#     #     sample_bytes = f.read()

#     # files = {
#     #     'sample': ('sample.mp3', sample_bytes),
#     # }

#     data = {
#         'access_key': access_key,
#         'data_type': data_type,
#         'signature_version': signature_version,
#         'signature': sign,
#         'timestamp': timestamp,
#     }

#     print(f"""
#             Access_key : {access_key}\n
#             Data_type : {data_type}\n
#             signature_version : {signature_version}\n
#             signature : {sign}\n
#             timestamp : {timestamp}
#           """)

#     with open(file_path, 'rb') as f:
#         print("Envoi du fichier:", file_path, "(", os.path.getsize(file_path), "bytes )")
#         files = {'sample': f}
#         response = requests.post(url, files=files, data=data)

#     # print(f"File size: {len(sample_bytes)} bytes")
#     # response = requests.post(url, files=files, data=data)
#     print("=== Status Code ===", response.status_code)
#     print("=== Réponse brute ===", response.json())

#     if response.status_code == 200:
#         result = response.json()
#         status_code = result.get("status", {}).get("code")
#         if status_code == 0:
#             metadata = result.get("metadata", {})
#             music_info = metadata.get("music", [{}])[0]
#             title = music_info.get("title")
#             artist = music_info.get("artists", [{}])[0].get("name")
#             return {"title": title, "artist": artist}
#         else:
#             return {"error": "Musique non reconnue ou hors base de données."}
#     else:
#         return {"error": f"Erreur API: {response.status_code} - {response.text}"}

# ///////////////////// Reconnsaissance avec ShazamIO /////////////////
# def _run_coroutine(coro):
#     """
#     Lance une coroutine de façon synchrone, même si on est déjà dans un event loop.
#     """
#     try:
#         loop = asyncio.get_event_loop()
#     except RuntimeError:
#         # Pas d’event loop courant
#         return asyncio.run(coro)

#     if loop.is_running():
#         # Crée un nouveau loop pour exécuter la coroutine
#         new_loop = asyncio.new_event_loop()
#         try:
#             return new_loop.run_until_complete(coro)
#         finally:
#             new_loop.close()
#     else:
#         return loop.run_until_complete(coro)

# def recognize_music_with_shazamio(file_path: str) -> dict:
#     """
#     Reconnaît un extrait audio via Shazam (sans API key).

#     Args:
#         file_path (str): Chemin vers le fichier audio (MP3, WAV, etc).

#     Returns:
#         dict: {'title': ..., 'artist': ...} ou {'error': ...}.
#     """
#     async def _async_recognize():
#         shazam = Shazam()
#         out = await shazam.recognize_song(file_path)
#         track = out.get('track')
#         if not track:
#             return {"error": "Musique non reconnue par Shazamio."}
#         return {
#             "title": track.get('title'),
#             "artist": track.get('subtitle')
#         }

#     try:
#         return _run_coroutine(_async_recognize())
#     except Exception as e:
#         return {"error": f"Erreur Shazamio: {e}"}
    
# //////////////////////////////////////////////////////
    

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


@router.post("/lyrics/play-realtime")
async def play_lyrics(data: LyricsModel, current_user = Depends(get_current_user)):
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
    audio_file = await record_and_get_path(durée=10)
    if audio_file != 0:
        print("Fichier Audio créer et enregistré !")

    # Envoyer le Son à l'API AudD et récupérer Titre + Artiste
    meta_data = recognize_music_with_audd(audio_file)
    # meta_data = recognize_music_with_acrcloud(audio_file)
    # meta_data = recognize_music_with_shazamio(audio_file)
    print(f"Titre et Artiste reconnu : {meta_data}")

    # chanson1 = {'title': "La vie qu'on mène", 'artist': 'Ninho'}

    # Récupération des Paroles de la chanson détectée
    lyrics_data = get_lyrics(meta_data)
    # lyrics_data = {'lyrics': "No me importa lo que de mí se diga\r\nVida usted su vida, que yo vivo la mia\r\nQue solo es una, disfruta el momento\r\nQue el tiempo se acaba y pa'trás no vira\r\nBebiendo, fumando y jodiendo\n\nSigo vacilando de party to' los día'\n\nSíguelo, oh-oh-oh, oh-oh-oh, oh-oh (¡Farru!)\n\nSíguelo, oh-oh-oh, oh-oh-oh, oh-oh (La rola y pepa)\n\n\n\nPepa y agua pa' la seca\n\nTo' el mundo en pastilla en la discoteca\n\nPepa y agua pa' la seca\n\nTo' el mundo en pastilla en la discoteca\n\n\n\nDesacata'o\n\nEmpastilla'o\n\n(Qué maldita nota)\n\n(Arcoíris)\n\n¡Fa-Farru!\n\n\n\n"}
    print(f"Les Lyrics du son capté : {lyrics_data}")

    # Découpage et envoie des Paroles par blocs via MQTT
    playing_lyrics = asyncio.create_task(play_lyrics_blocks(lyrics_data, MQTT_TOPIC))

    return {"status": "ok"}


# UPLOAD_DIR_LYRICS = Path("./app/uploads/lyrics")
# UPLOAD_DIR_LYRICS.mkdir(parents=True, exist_ok=True)

LRC_PATH = UPLOAD_DIR_LYRICS / "jetemmeneauvent_lyrics.lrc"

playing_lyrics: Union[asyncio.Task, None] = None

def parse_lrc(path: Path) -> list[tuple[float, str]]:
    """
    Lit un fichier .lrc et renvoie une liste triée de (timestamp_en_secondes, texte).
    """
    pattern = re.compile(r'^\[(\d{2}):(\d{2}\.\d{2})\](.*)$')
    entries = []
    for line in path.read_text(encoding="utf-8").splitlines():
        m = pattern.match(line)
        if m:
            minutes = int(m.group(1))
            seconds = float(m.group(2))
            text = m.group(3).strip()
            entries.append((minutes * 60 + seconds, text))
    # Assure l’ordre croissant
    return sorted(entries, key=lambda x: x[0])

async def play_lyrics_from_lrc(topic: str):
    """
    Parcourt les entrées (timestamp, text) et publie chaque text au bon moment.
    """
    sync_map = parse_lrc(LRC_PATH)
    start = asyncio.get_event_loop().time()

    for ts, text in sync_map:
        # Attendre jusqu’au timestamp relatif
        now = asyncio.get_event_loop().time()
        delay = (start + ts) - now
        if delay > 0:
            await asyncio.sleep(delay)
        
        clean_lyrics = strip_accents(text)

        payload = {
            "FLAG": "LYRICS_BLOCK",
            "time": ts,
            "text": clean_lyrics
        }
        publish(topic, payload)
        print(f"[{ts:06.2f}] → {text}")

    # Fin de lecture
    publish(topic, {"FLAG": "LYRICS_STOP"})
    print("🎉 Lecture terminée")

@router.post("/lyrics/play-hardcoded")
async def play_lyrics(data: LyricsModel, current_user=Depends(get_current_user)):
    global playing_lyrics

    # Si une tâche est déjà en cours, on l’annule
    if playing_lyrics and not playing_lyrics.done():
        playing_lyrics.cancel()
        try:
            await playing_lyrics
        except asyncio.CancelledError:
            print("✂️ Ancienne tâche annulée")

    # Indique au client qu’on démarre
    publish(MQTT_TOPIC, {"FLAG": "LYRICS_PLAY", **data.dict()})
    print("▶️ Démarrage de la lecture des lyrics")

    # Lance la playback task
    playing_lyrics = asyncio.create_task(play_lyrics_from_lrc(MQTT_TOPIC))

    return {"status": "ok", "message": "Lecture lancée, calée sur le LRC"}



@router.post("/lyrics/stop")
async def stop_lyrics(current_user=Depends(get_current_user)):
    global playing_lyrics

    if playing_lyrics and not playing_lyrics.done():
        playing_lyrics.cancel()
        try:
            await playing_lyrics
        except asyncio.CancelledError:
            print("✂️ Tâche lyrics annulée")

    publish(MQTT_TOPIC, {"FLAG": "LYRICS_STOP"})
    print("⏹️ Lecture stoppée")
    return {"status": "ok", "message": "Lecture stoppée"}


# ######################################## ADS #########################################
@router.post("/ads/play")
async def play_ads(data: AdsModel):
    if data.state != "play":
        return {"status": "error", "detail": "Pas le bon état pour PLAY !"}
    
    if data.state == "play":
        print(f"Contenu du message : {data.content}")
        print(f"State = {data.state}")
        clean_content = strip_accents(data.content)
        payload = { "FLAG": "ADS_PLAY", **data.dict(), "content": clean_content } # Faire en sorte d'exclure la balise 'state' !
        publish(MQTT_TOPIC, payload)
        print(f"Le payload du message envoyé : {payload}")
    else:
        return "Pas le bon état pour PLAY !"
    return {"status": "ok"}

@router.post("/ads/stop")
async def stop_ads(data: AdsModel):
    if data.state != "stop":
        return {"status": "error", "detail": "Pas le bon état pour STOP !"}
    
    if data.state == "stop":
        print(f"Arrêt de l'affichage du message : {data.content} !!")
        print(f"State = {data.state}")
        publish(MQTT_TOPIC, { "FLAG": "ADS_STOP" })
    else:
        print(f"Erreur lors de la condition ! Pas le bon état pour STOP ! State = {data.state}")
    return {"status": "ok"}
