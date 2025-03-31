import asyncio
import websockets
import json
from typing import Dict, Optional

# Configuration du client WebSocket
ESP_MASTER_IP = "192.168.1.1"  # IP de l'ESP Père
ESP_MASTER_PORT = 81  # Port WebSocket de l'ESP Père
ws_connection: Optional[websockets.WebSocketClientProtocol] = None

async def connect_websocket():
    """Établit une connexion WebSocket avec l'ESP Père"""
    global ws_connection
    try:
        ws_connection = await websockets.connect(f"ws://{ESP_MASTER_IP}:{ESP_MASTER_PORT}")
        print("Connecté au serveur WebSocket de l'ESP Père!")
        return ws_connection
    except Exception as e:
        print(f"Erreur de connexion WebSocket: {e}")
        return None

async def get_connection():
    """Récupère la connexion WebSocket existante ou en crée une nouvelle"""
    global ws_connection
    
    # Vérification plus robuste de l'état de la connexion
    is_closed = False
    if ws_connection is not None:
        try:
            # Utilisation d'une vérification alternative
            # Soit en utilisant une propriété différente
            is_closed = not ws_connection.open
        except AttributeError:
            try:
                # Dans certaines versions, on peut utiliser une méthode
                is_closed = ws_connection.state != 1  # 1 souvent utilisé pour OPEN
            except (AttributeError, TypeError):
                # En cas d'échec, on considère la connexion comme fermée pour sécurité
                is_closed = True
    
    if ws_connection is None or is_closed:
        return await connect_websocket()
    
    return ws_connection

async def send_message(message: str):
    """Envoie un message à l'ESP Père via WebSocket"""
    connection = await get_connection()
    if connection:
        try:
            await connection.send(message)
            print(f"Message envoyé: {message}")
            return True
        except Exception as e:
            print(f"Erreur d'envoi de message: {e}")
            ws_connection = None
            return False
    return False

# Pour maintenir la connexion active et gérer la réception des messages
async def websocket_listener():
    """Boucle d'écoute des messages du serveur WebSocket"""
    while True:
        connection = await get_connection()
        if connection:
            try:
                message = await connection.recv()
                print(f"Message reçu: {message}")
                # Vous pouvez traiter les messages reçus ici si nécessaire
            except websockets.exceptions.ConnectionClosed:
                print("Connexion WebSocket fermée")
                ws_connection = None
                await asyncio.sleep(5)  # Attendre avant de tenter une reconnexion
            except Exception as e:
                print(f"Erreur de réception: {e}")
                ws_connection = None
                await asyncio.sleep(5)
        else:
            await asyncio.sleep(5)  # Attendre avant de tenter une reconnexion
