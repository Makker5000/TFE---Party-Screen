import os
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from supabase import create_client
from datetime import datetime, timedelta
from uuid import uuid4
from dotenv import load_dotenv
import jwt

# --- Chargement des variables d'environnement ---
load_dotenv(dotenv_path=".env")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
JWT_SECRET = os.getenv("JWT_SECRET")

# Initialise le client Supabase avec la clé service-role
sb = create_client(SUPABASE_URL, SUPABASE_KEY)
app = FastAPI()
auth = HTTPBearer()

# --- CORS si frontend sur un autre port ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ou restreins à ["http://localhost:5173"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Fonctions JWT ---
def create_token(user_id: str) -> str:
    payload = {
        "sub": user_id,
        "exp": datetime.utcnow() + timedelta(hours=6)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")

def decode_token(token: str) -> str:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        return payload.get("sub")
    except jwt.PyJWTError:
        raise HTTPException(status_code=403, detail="Token invalide ou expiré")

# --- Endpoint: création de session guest + JWT ---
@app.post("/api/login")
def login_accept_terms():
    # Crée un user invité et retourne un JWT
    user_id = str(uuid4())
    sb.table('users').insert({
        'id': user_id,
        'accepted_terms': True
    }).execute()
    token = create_token(user_id)
    return {"token": token}

# --- Mémoire simple pour suivre les IP votantes (ou mettre en DB) ---
user_votes = {}

# --- GET /api/tracks ---
@app.get("/api/tracks")
def get_tracks():
    resp = sb.table('tracks').select('track_id, title, artist').execute()
    return resp.data

# --- POST /api/vote/{track_id} ---
# @app.post("/api/vote/{track_id}")
# def vote(track_id: int, request: Request):

#     user_ip = request.client.host

#     # Anti-spam simple : max 3 votes par IP par 6h
#     now = datetime.utcnow()
#     user_data = user_votes.get(user_ip, [])
#     user_data = [t for t in user_data if t > now - timedelta(hours=6)]

#     if len(user_data) >= 3:
#         raise HTTPException(status_code=403, detail="3 votes max par 6h.")

#     # Vérifie si l'utilisateur existe dans Supabase
#     existing_user = sb.table('users').select('id').eq('id', user_ip).execute()

#     if not existing_user.data:
#         # L'utilisateur n'existe pas, on l'ajoute
#         sb.table('users').insert({'id': user_ip}).execute()

#     # Enregistre le vote
#     vote_resp = sb.table('votes').insert({
#         'track_id': track_id,
#         'user_id': user_ip
#     }).execute()

#     user_data.append(now)
#     user_votes[user_ip] = user_data

#     return {'success': True}

@app.post("/api/vote/{track_id}")
def vote(track_id: int, credentials: HTTPAuthorizationCredentials = Depends(auth)):
    user_id = decode_token(credentials.credentials)

    # Limite à 3 votes par 6h
    time_limit = datetime.utcnow() - timedelta(hours=6)
    resp = sb.table('votes') \
        .select('id', count='exact') \
        .eq('user_id', user_id) \
        .gte('timestamp', time_limit.isoformat()) \
        .execute()

    if (resp.count or 0) >= 3:
        raise HTTPException(status_code=403, detail="Limite de 3 votes atteinte")

    # Enregistre le vote
    sb.table('votes').insert({
        'track_id': track_id,
        'user_id': user_id,
        'timestamp': datetime.utcnow().isoformat()
    }).execute()

    return {'success': True}

# --- GET /api/stats ---
@app.get("/api/stats")
def stats():
    # user_id = decode_token(credentials.credentials)
    # Étape 1 : récupérer les votes groupés par track_id
    resp_votes = sb.table('votes') \
        .select('track_id', count='exact') \
        .execute()

    if not resp_votes.data:
        return {}

    # Construire un mapping : track_id -> count
    vote_counts = {}
    for vote in resp_votes.data:
        track_id = vote['track_id']
        vote_counts[track_id] = vote_counts.get(track_id, 0) + 1

    # Étape 2 : récupérer toutes les infos des tracks correspondantes
    track_ids = list(vote_counts.keys())
    resp_tracks = sb.table('tracks').select('track_id', 'title', 'artist').in_('track_id', track_ids).execute()

    # Étape 3 : construire le JSON final
    stats_result = {}
    for track in resp_tracks.data:
        key = f"{track['title']} - {track['artist']}"
        stats_result[key] = vote_counts.get(track['track_id'], 0)

    return stats_result

# --- POST /api/session ---
@app.post("/api/session")
def create_session(tracks: list[dict], credentials: HTTPAuthorizationCredentials = Depends(auth)):
    sb.table('votes').delete().neq('id', None).execute()
    sb.table('tracks').delete().neq('track_id', None).execute()
    sb.table('tracks').insert(tracks).execute()
    return {'session_created': True}