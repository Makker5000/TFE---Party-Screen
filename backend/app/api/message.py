from fastapi import APIRouter
from pydantic import BaseModel
from app.utils.mqtt import publish_message

router = APIRouter()

class MessageModel(BaseModel):
    message: str

@router.post("/send_message/")
async def send_message(data: MessageModel):
    # Publier sur MQTT
    message = data.message
    topic = "topic/esp8266"
    publish_message(topic, message)
    return {"status": "Message envoyé", "message": message}
