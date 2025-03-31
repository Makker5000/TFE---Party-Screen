from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
import asyncio
from app.utils.websockets import send_message

router = APIRouter()

class MessageModel(BaseModel):
    message: str

@router.post("/send_message/")
async def send_message_api(data: MessageModel):
    # Envoyer via WebSocket au lieu de MQTT
    success = await send_message(data.message)
    if success:
        return {"status": "Message envoyé", "message": data.message}
    else:
        return {"status": "Erreur d'envoi", "message": data.message}

# Endpoint WebSocket pour les clients web (frontend SvelteKit)
@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            # Recevoir le message du client web
            data = await websocket.receive_text()
            
            # Envoyer le message à l'ESP Père
            success = await send_message(data)
            
            # Répondre au client web
            if success:
                await websocket.send_json({"status": "Message envoyé", "message": data})
            else:
                await websocket.send_json({"status": "Erreur d'envoi", "message": data})
    except WebSocketDisconnect:
        print("Client déconnecté")
