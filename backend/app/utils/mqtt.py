# import paho.mqtt.client as mqtt

# # 📡 Configuration du broker Mosquitto
# BROKER_IP = "127.0.0.1"  # Mets l'IP de ton Orange Pi
# BROKER_PORT = 1883
# # MQTT_TOPIC = "topic/esp8266"

# # 🛰 Connexion au broker
# client = mqtt.Client()

# def connect_mqtt():
#     try:
#         client.connect(BROKER_IP, BROKER_PORT, 60)
#         print("Connecté au Borker MQTT !")
#     except Exception as e:
#         print("Erreur de connexion au MQTT :", e)

# def publish_message(topic, message: str):
#     connect_mqtt()
#     client.publish(topic, message)
#     print(f"Message envoyé sur le topic {topic} : {message}")

# connect_mqtt()

import paho.mqtt.client as mqtt
from app.core.config import MQTT_BROKER, MQTT_PORT, MQTT_TOPIC

client = mqtt.Client()

def connect_mqtt():
    try:
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
    except Exception as e:
        print(f"[MQTT ERROR] Connexion échouée : {e}")

def publish(topic: str, payload: dict):
    connect_mqtt()
    import json
    message = json.dumps(payload)
    client.publish(topic, message)
    print(f"[MQTT] Message publié sur {topic} : {message}")
