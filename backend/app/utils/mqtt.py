# import paho.mqtt.client as mqtt
# from app.core.config import MQTT_BROKER, MQTT_PORT, MQTT_TOPIC

# client = mqtt.Client()

# def connect_mqtt():
#     try:
#         client.connect(MQTT_BROKER, MQTT_PORT, 60)
#     except Exception as e:
#         print(f"[MQTT ERROR] Connexion échouée : {e}")

# def publish(topic: str, payload: dict):
#     connect_mqtt()
#     import json
#     message = json.dumps(payload)
#     client.publish(topic, message)
#     print(f"[MQTT] Message publié sur {topic} : {message}")


import paho.mqtt.client as mqtt
import ssl
import json
from app.core.config import MQTT_BROKER, MQTT_PORT, MQTT_TOPIC, CA_CERT_PATH, CLIENT_CERT, CLIENT_KEY

client = mqtt.Client()

# Chargement du certificat CA pour vérifier le broker
client.tls_set(
    ca_certs=CA_CERT_PATH,
    certfile=CLIENT_CERT,       # ou "path/to/client.crt" si mutual TLS
    keyfile=CLIENT_KEY,        # ou "path/to/client.key"
    tls_version=ssl.PROTOCOL_TLSv1_2,
    ciphers=None
)
# Si votre broker a un certificat self-signed et que vous êtes en dev :
client.tls_insecure_set(True)

def connect_mqtt():
    try:
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
    except Exception as e:
        print(f"[MQTT ERROR] Connexion TLS échouée : {e}")

def publish(topic: str, payload: dict):
    connect_mqtt()
    message = json.dumps(payload)
    client.publish(topic, message)
    client.disconnect()
    print(f"[MQTT] Message publié sur {topic} : {message}")