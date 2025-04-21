import paho.mqtt.client as mqtt

# 📡 Configuration du broker Mosquitto
BROKER_IP = "127.0.0.1"  # Mets l'IP de ton Orange Pi
BROKER_PORT = 1883
# MQTT_TOPIC = "topic/esp8266"
MQTT_TOPIC = "esp/pere/commande"

# 🛰 Connexion au broker
client = mqtt.Client()

def connect_mqtt():
    try:
        client.connect(BROKER_IP, BROKER_PORT, 60)
        print("Connecté au Borker MQTT !")
    except Exception as e:
        print("Erreur de connexion au MQTT :", e)

def publish_message(topic, message: str):
    connect_mqtt()
    client.publish(topic, message)
    print(f"Message envoyé sur le topic {topic} : {message}")

connect_mqtt()
