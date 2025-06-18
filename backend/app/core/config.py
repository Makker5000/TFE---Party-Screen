# MQTT_BROKER = "mon.broker.mqtt"
MQTT_BROKER = "192.168.1.10"
MQTT_PORT = 8883
# MQTT_TOPIC = "topic/esp8266"  # utilisé si pas de topic dynamique
MQTT_TOPIC = "esp/pere/commande"  # utilisé si pas de topic dynamique
CA_CERT_PATH    = "/etc/mosquitto/certs/ca.crt"
CLIENT_CERT     = "/etc/mosquitto/certs/CA_backend_client/backend-client.crt"
CLIENT_KEY      = "/etc/mosquitto/certs/CA_backend_client/backend-client.key"