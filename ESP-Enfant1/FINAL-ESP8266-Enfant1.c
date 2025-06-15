#include <ESP8266WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include <Adafruit_NeoMatrix.h>
#include <Adafruit_NeoPixel.h>
#include <stdio.h>
#include <EEPROM.h>

// ─────── CONFIGURATION EEPROM ────────────────────────────────────────────────
#define ADDR_CONFIGURED    0
#define ADDR_SCREEN_WIDTH  1
#define ADDR_SCREEN_HEIGHT 2
#define EEPROM_SIZE        16

// ─── CONFIGURATION GÉNÉRALE ────────────────────────────────────────────────
#define CHILD_NUM       1    // ← À changer pour chaque ESP (1,2,3...)
const char* WIFI_SSID   = "MonReseauESP";
const char* WIFI_PASS   = "ouiouioui";
const char* MQTT_BROKER = "192.168.1.10";
const uint16_t MQTT_PORT= 1883;
// const uint16_t MQTT_PORT= 8883; // <-- Port pour MQTTS
#define MQTT_MAX_PACKET_SIZE 8192

// Certificat CA du broker (copie du ca.crt en format PEM)
// const char* ca_cert = \
// "-----BEGIN CERTIFICATE-----\n" \
// "MIID... (ton contenu ici)\n" \
// "-----END CERTIFICATE-----\n";

// Topics construits dynamiquement
String TOPIC_CMD;
String TOPIC_STATUS;

// Matrice NeoPixel
#define PIN_MATRIX     D5
#define MAT_W          112 // 96 = 6 matrices en ligne, sinon je peux mettre un peu plus
#define MAT_H          16
#define MATRIX_SIZE    16
Adafruit_NeoMatrix matrix(
  MAT_W, MAT_H, PIN_MATRIX,
  NEO_MATRIX_TOP+NEO_MATRIX_LEFT+NEO_MATRIX_COLUMNS+NEO_MATRIX_ZIGZAG,
  NEO_GRB+NEO_KHZ800
);

int SCREEN_WIDTH = 48;
int SCREEN_HEIGHT = 16;
int screenMatrixCount = SCREEN_WIDTH / MATRIX_SIZE;
int realMatrixCount   = MAT_W / MATRIX_SIZE;

// ─── BUFFERS GLOBAUX ────────────────────────────────────────────────────────
uint8_t  imageBuffer[MAT_W * MAT_H * 3];
bool     imageBufferValid = false;

// Paramètres QR
#define QR_MODULE_BLACK_R   255    
#define QR_MODULE_BLACK_G   255
#define QR_MODULE_BLACK_B   255
#define QR_MODULE_WHITE_R   0     
#define QR_MODULE_WHITE_G   0      
#define QR_MODULE_WHITE_B   0     

// État des animations
struct LyricsState {
  uint16_t textColor, bgColor;
  String animation;
  String text;
  bool active;
  int scrollX;
};
LyricsState lyrics;

struct AdsState {
  uint16_t textColor, bgColor;
  String animation;
  const char* content;
  float speed;
  bool active;
  int scrollX;
};
AdsState ads;

struct WaitingAnimation {
  bool active;
  int phase;
  int direction;
  unsigned long lastUpdate;
  int textX;
  int bgPhase;
  const char* text = "Waiting...";
  int text_width = 60;
};
WaitingAnimation waitingAnim;

struct PowerAnimation {
  bool active;
  bool isOn;
  int phase;
  int brightness;
  unsigned long lastUpdate;
  String text;
};
PowerAnimation powerAnim;

struct FadeAnimation {
  bool active;
  bool fadeIn;
  int startBrightness;
  int targetBrightness;
  int currentBrightness;
  unsigned long startTime;
  unsigned long duration;
  bool shouldStartWaiting;
};
FadeAnimation fadeAnim;

// MQTT client avec buffer élargi
WiFiClient wifiClient;
PubSubClient mqtt(wifiClient);

// MQTTS client avec buffer élargi
// WiFiClientSecure wifiClient;
// PubSubClient mqtt(wifiClient);

unsigned long lastHeartbeat = 0;
unsigned long lastRender = 0;

// Données de Refresh
#define REFRESH_INTERVAL 2000

unsigned long lastRefresh = 0;
int previousRealMatrixCount = -1;

// Variable pour Config écran
bool   isConfigured = false;

// ─── PROTOTYPES ─────────────────────────────────────────────────────────────
void startupAnimation();
void startWaitingAnimation();
void stopWaitingAnimation();
void renderWaitingAnimation();
void startPowerAnimation(bool isOn);
void startFadeAnimation(bool fadeIn, unsigned long duration);
void renderPowerAnimation();

void updateFadeAnimation();

void setupWiFi();
void setupMQTT();
void mqttCallback(char* topic, byte* payload, unsigned int length);
void reconnectMQTT();
void sendHeartbeat();

// Handlers des commandes
void handleVisualPlay(const JsonDocument& doc);
void handleVisualStop();
void handleQRPlay(const JsonDocument& doc);
void handleQRStop();
void handleLyricsPlay(const JsonDocument& doc);
void handleLyricsBlock(const JsonDocument& doc);
void handleLyricsStop();
void handleAdsPlay(const JsonDocument& doc);
void handleAdsStop();
void handleBrightness(const JsonDocument& doc);

void handlePowerOff();
void handlePowerOn();
void handleClear();
void handleConfig(const JsonDocument& doc);

// Rendu
void updateDisplay();
void renderLyrics();
void renderAds();
void renderDefault();
void renderMatrixOut(int startMatrix, int matrixCount);
void refreshMatrixOutIfNeeded();
void refreshVisualIfNeeded();

// Utilitaires
int base64Decode(const char* input, uint8_t* output, size_t maxOutputSize);
uint16_t mapColor(const String& name);
uint16_t colorWheel(uint8_t pos);
void verifConfig();

// ─── ANIMATIONS ─────────────────────────────────────────────────────────────────
void startupAnimation() {
  Serial.println("🌈 Animation de démarrage...");
  
  matrix.clear();
  
  // Balayage coloré pour identifier l'ESP
  uint32_t colors[] = {
    matrix.Color(255, 0, 0),    // Rouge
    matrix.Color(0, 255, 0),    // Vert
    matrix.Color(0, 0, 255),    // Bleu
    matrix.Color(255, 255, 0),   // Jaune
    matrix.Color(255, 0, 255),   // Magenta
    matrix.Color(0, 255, 255),   // Cyan
    matrix.Color(255, 128, 0),   // Orange
    matrix.Color(128, 0, 255)    // Violet
  };
  
  uint32_t myColor = colors[(CHILD_NUM - 1) % 8];
  
  // Balayage horizontal
  for (int x = 0; x < 48; x++) {
    matrix.clear();
    for (int y = 0; y < 16; y++) {
      matrix.drawPixel(x, y, myColor);
    }
    matrix.show();
    delay(20);
  }
  
  // Afficher le numéro de l'ESP (simple)
  matrix.clear();
  matrix.setTextColor(myColor);
  matrix.setTextSize(1);
  // matrix.setCursor(20, 4);
  // matrix.print(CHILD_NUM);
  int16_t x1,y1; uint16_t w,h;
  matrix.getTextBounds(String(CHILD_NUM),0,0,&x1,&y1,&w,&h);
  int16_t x = (SCREEN_WIDTH - w)/2;
  int16_t y = (SCREEN_HEIGHT - h)/2;
  matrix.setCursor(x, y);
  matrix.print(String(CHILD_NUM));
  
  matrix.show();
  delay(2000);
  
  matrix.clear();
  matrix.show();
}

// ─── ANIMATION "WAITING" ───────────────────────────────────────────────────
void startWaitingAnimation() {
  waitingAnim.active = true;
  waitingAnim.phase = 0;
  waitingAnim.direction = 1;
  waitingAnim.lastUpdate = millis();
  waitingAnim.textX = SCREEN_WIDTH;
  waitingAnim.bgPhase = 0;
  Serial.println("🔄 Animation Waiting démarrée");
  renderWaitingAnimation();
}

void stopWaitingAnimation() {
  waitingAnim.active = false;
  Serial.println("🛑 Animation Waiting arrêtée");
}

void renderWaitingAnimation() {
  if (!waitingAnim.active) return;
  
  unsigned long now = millis();
  if (now - waitingAnim.lastUpdate < 10) return; // 80ms = ~12 FPS
  
  waitingAnim.lastUpdate = now;
  
  // Animation du fond avec vague de couleur
  // matrix.fillScreen(matrix.Color(0, 32, 64));
  
  // Créer une vague de couleur en arrière-plan
  // for (int x = 0; x < SCREEN_WIDTH; x++) {
  //   for (int y = 0; y < SCREEN_HEIGHT; y++) {
  //     float wave = sin((x + waitingAnim.bgPhase) * 0.6) * 127 + 128;
  //     int intensity = (int)constrain(wave, 5, 70);
  //     uint32_t bgColor = matrix.Color(intensity, 10, 0); // Bleu-cyan subtil
  //     matrix.drawPixel(x, y, bgColor);
  //   }
  // }

  // 1) Étendue maximale du dégradé en diagonale
  const int maxDiag = SCREEN_WIDTH + SCREEN_HEIGHT - 2;  

  // 2) Avance du dégradé (0 → maxDiag)
  int phase = waitingAnim.bgPhase % (maxDiag + 1);

  // 3) Deux couleurs de coin à coin (modifiable)
  uint8_t r1 = 139, g1 = 0,   b1 = 139;    // coin bas-droite : rouge
  uint8_t r2 = 128,   g2 = 64,   b2 = 0;  // coin haut-gauche : bleu

  // 4) Pour chaque pixel, on calcule sa "distance diagonale" x+y
  for (int x = 0; x < SCREEN_WIDTH; x++) {
    for (int y = 0; y < SCREEN_HEIGHT; y++) {
      // distance sur l'axe diag
      int d = x + y;  
      // on fait glisser le profil : d_shift = (d + phase) mod (maxDiag+1)
      int d_shift = (d + phase) % (maxDiag + 1);
      // ratio entre 0 (bleu) et 1 (rouge)
      // float t = float(d_shift) / float(maxDiag + 5);
      float u = float(d_shift) / float(maxDiag);
      float t = (1.0 - cos(u * PI)) * 0.5;

      // interpolation linéaire R,G,B
      uint8_t r = r1 * t + r2 * (1.0 - t);
      uint8_t g = g1 * t + g2 * (1.0 - t);
      uint8_t b = b1 * t + b2 * (1.0 - t);

      matrix.drawPixel(x, y, matrix.Color(r, g, b));
    }
  }

  // ----- Essai d'afficher seulement sur les matrices valides (NON FONCTIONNEL --> texte ne s'affiche pas) ------
  if (waitingAnim.textX > -waitingAnim.text_width && waitingAnim.textX < SCREEN_WIDTH) {
    const int CHAR_W = 6;  // largeur d'un caractère en pixels (avec espacement)
    int len = strlen(waitingAnim.text);
    int textStart = waitingAnim.textX;
    int textEnd = textStart + waitingAnim.text_width;
    
    // Si le texte dépasse la zone configurée à droite, on le tronque
    if (textEnd > SCREEN_WIDTH) {
      // Calculer combien de caractères on peut afficher
      int visibleWidth = SCREEN_WIDTH - textStart;
      int visibleChars = visibleWidth / CHAR_W;
      
      if (visibleChars > 0 && visibleChars <= len) {
        // Créer une sous-chaîne avec seulement les caractères visibles
        char tempText[32];
        strncpy(tempText, waitingAnim.text, visibleChars);
        tempText[visibleChars] = '\0';
        
        matrix.setTextColor(matrix.Color(255, 255, 255));
        matrix.setTextSize(1);
        matrix.setTextWrap(false);
        matrix.setCursor(waitingAnim.textX, 4);
        matrix.print(tempText);
      }
    } else {
      // Le texte tient entièrement dans la zone configurée
      matrix.setTextColor(matrix.Color(255, 255, 255));
      matrix.setTextSize(1);
      matrix.setTextWrap(false);
      matrix.setCursor(waitingAnim.textX, 4);
      matrix.print(waitingAnim.text);
    }
  }
  
  // Texte "Waiting..." qui défile
  // matrix.setTextColor(matrix.Color(255, 255, 255));
  // matrix.setTextSize(1);
  // matrix.setTextWrap(false);
  // matrix.setCursor(waitingAnim.textX, 4);
  // matrix.print(waitingAnim.text);
  
  // Animation du texte (défilement)
  waitingAnim.textX--;
  if (waitingAnim.textX < -waitingAnim.text_width) { // "Waiting..." fait environ 60 pixels
    waitingAnim.textX = SCREEN_WIDTH;
  }
  
  // Phase de l'animation du fond
  // waitingAnim.bgPhase++;
  // if (waitingAnim.bgPhase > 628) waitingAnim.bgPhase = 0; // 2*PI*100 pour cycle complet
  // 6) Incrément de phase pour animer le dégradé
  waitingAnim.bgPhase++;
  
  matrix.show();
  refreshMatrixOutIfNeeded();
}

// ─── ANIMATIONS "ON" ET "OFF" ──────────────────────────────────────────────
void startPowerAnimation(bool isOn) {
  stopWaitingAnimation();

  powerAnim.active = true;
  powerAnim.isOn = isOn;
  powerAnim.phase = 0;
  powerAnim.brightness = isOn ? 0 : 255;
  powerAnim.lastUpdate = millis();
  powerAnim.text = isOn ? "ON" : "OFF";
  Serial.printf("⚡ Animation Power %s démarrée\n", isOn ? "ON" : "OFF");
}

void renderPowerAnimation() {
  if (!powerAnim.active) return;
  
  unsigned long now = millis();
  if (now - powerAnim.lastUpdate < 50) return; // 50ms = 20 FPS
  
  powerAnim.lastUpdate = now;
  
  if (powerAnim.isOn) {
    // Animation "ON" - Rideau qui s'ouvre + texte qui apparaît
    matrix.fillScreen(0);
    
    // Effet rideau qui s'ouvre (du centre vers les bords)
    int curtainPos = map(powerAnim.phase, 0, 100, SCREEN_WIDTH/2, 0);
    
    // Dessiner le "rideau" qui se retire
    for (int x = 0; x < curtainPos; x++) {
      for (int y = 0; y < SCREEN_HEIGHT; y++) {
        matrix.drawPixel(x, y, matrix.Color(20, 20, 20));
        matrix.drawPixel(SCREEN_WIDTH - 1 - x, y, matrix.Color(20, 20, 20));
      }
    }
    
    // Texte "ON" qui apparaît progressivement
    int textBrightness = map(powerAnim.phase, 30, 100, 0, 255);
    textBrightness = constrain(textBrightness, 0, 255);
    
    matrix.setTextColor(matrix.Color(0, textBrightness, 0)); // Vert
    matrix.setTextSize(1);
    
    // Centrer le texte "ON"
    int16_t x1, y1; uint16_t w, h;
    matrix.getTextBounds("ON", 0, 0, &x1, &y1, &w, &h);
    int16_t x = (SCREEN_WIDTH - w) / 2;
    int16_t y = (SCREEN_HEIGHT - h) / 2;
    matrix.setCursor(x, y);
    matrix.print("ON");
    
  } else {
    // Animation "OFF" - Rideau qui se ferme + texte qui disparaît
    matrix.fillScreen(0);
    
    // Texte "OFF" qui disparaît progressivement
    int textBrightness = map(powerAnim.phase, 0, 70, 255, 0);
    textBrightness = constrain(textBrightness, 0, 255);
    
    matrix.setTextColor(matrix.Color(textBrightness, 0, 0)); // Rouge
    matrix.setTextSize(1);
    
    // Centrer le texte "OFF"
    int16_t x1, y1; uint16_t w, h;
    matrix.getTextBounds("OFF", 0, 0, &x1, &y1, &w, &h);
    int16_t x = (SCREEN_WIDTH - w) / 2;
    int16_t y = (SCREEN_HEIGHT - h) / 2;
    matrix.setCursor(x, y);
    matrix.print("OFF");
    
    // Effet rideau qui se ferme (des bords vers le centre)
    int curtainPos = map(powerAnim.phase, 30, 100, 0, SCREEN_WIDTH/2);
    
    for (int x = 0; x < curtainPos; x++) {
      for (int y = 0; y < SCREEN_HEIGHT; y++) {
        matrix.drawPixel(x, y, matrix.Color(20, 20, 20));
        matrix.drawPixel(SCREEN_WIDTH - 1 - x, y, matrix.Color(20, 20, 20));
      }
    }
  }
  
  matrix.show();
  
  // Progression de l'animation
  powerAnim.phase += 2;
  if (powerAnim.phase >= 100) {
    powerAnim.active = false;
    Serial.printf("✅ Animation Power %s terminée\n", powerAnim.isOn ? "ON" : "OFF");
  }
}

// ─── ANIMATION DE FADE (LUMINOSITÉ PROGRESSIVE) ────────────────────────────
void startFadeAnimation(bool fadeIn, unsigned long duration = 1000) {
  fadeAnim.active = true;
  fadeAnim.fadeIn = fadeIn;
  fadeAnim.startBrightness = matrix.getBrightness(); // Prendre la luminosité actuelle
  fadeAnim.targetBrightness = fadeIn ? 50 : 10; // Luminosité cible
  fadeAnim.currentBrightness = fadeAnim.startBrightness;
  fadeAnim.startTime = millis();
  fadeAnim.duration = duration;
  fadeAnim.shouldStartWaiting = !fadeIn; // Si fade out, redémarrer waiting après
  
  Serial.printf("🌅 Animation Fade %s démarrée (%lu ms) - de %d à %d\n", 
                fadeIn ? "IN" : "OUT", duration, fadeAnim.startBrightness, fadeAnim.targetBrightness);
}

void updateFadeAnimation() {
  if (!fadeAnim.active) return;
  
  unsigned long elapsed = millis() - fadeAnim.startTime;
  
  if (elapsed >= fadeAnim.duration) {
    // Animation terminée
    fadeAnim.currentBrightness = fadeAnim.targetBrightness;
    matrix.setBrightness(fadeAnim.currentBrightness);
    fadeAnim.active = false;
    
    // Si c'était un fade out, redémarrer l'animation waiting
    if (fadeAnim.shouldStartWaiting) {
      Serial.println("🔄 Redémarrage animation waiting après fade out");
      startWaitingAnimation();
    }
    
    Serial.printf("✅ Animation Fade terminée (luminosité: %d)\n", 
                  fadeAnim.currentBrightness);
  } else {
    // Interpolation linéaire
    float progress = (float)elapsed / fadeAnim.duration;
    fadeAnim.currentBrightness = fadeAnim.startBrightness + 
      (fadeAnim.targetBrightness - fadeAnim.startBrightness) * progress;
    matrix.setBrightness(fadeAnim.currentBrightness);
  }
}

// ─── HELPERS POUR UTILISER LES ANIMATIONS ──────────────────────────────────
void playPowerOnAnimation() {
  // Arrêter l'animation waiting si elle est active
  stopWaitingAnimation();
  // Démarrer l'animation ON avec fade
  startFadeAnimation(true, 800);
  startPowerAnimation(true);
}

void playPowerOffAnimation() {
  // Démarrer l'animation OFF avec fade
  startFadeAnimation(false, 800);
  startPowerAnimation(false);
}

// Fonction pour démarrer une fonctionnalité avec animation
void startFeatureWithAnimation() {
  stopWaitingAnimation();
  startFadeAnimation(true, 600);
}

// Fonction pour arrêter une fonctionnalité avec animation
void stopFeatureWithAnimation() {
  startFadeAnimation(false, 400);
  // Programmer le retour à l'animation waiting après le fade
  // On va utiliser une variable pour ça
}

// ─── SETUP ─────────────────────────────────────────────────────────────────
void setup() {
  Serial.begin(115200);
  Serial.println();
  Serial.printf("🚀 ESP8266 Enfant #%d - Démarrage...\n", CHILD_NUM);
  
  // Construction des topics
  TOPIC_CMD    = "esp/enfant" + String(CHILD_NUM) + "/command";
  TOPIC_STATUS = "esp/enfant" + String(CHILD_NUM) + "/status";
  
  Serial.printf("📡 Topics: CMD='%s', STATUS='%s'\n", TOPIC_CMD.c_str(), TOPIC_STATUS.c_str());
  
  // Initialisation matrice
  matrix.begin();
  matrix.setBrightness(50);
  matrix.fillScreen(0);
  matrix.show();
  Serial.println("🎨 Matrice initialisée");
  
  // Initialisation états
  lyrics.active = false;
  ads.active = false;

  waitingAnim.active = false;
  powerAnim.active = false;
  fadeAnim.active = false;
  fadeAnim.shouldStartWaiting = false;

  EEPROM.begin(EEPROM_SIZE);
  loadConfig();
  
  // Connexions
  setupWiFi();
  setupMQTT();

  startupAnimation();

  startWaitingAnimation();
  
  Serial.println("✅ Initialisation terminée");
  sendHeartbeat();
}

// ─── LOOP ──────────────────────────────────────────────────────────────────
void loop() {
  // Maintenir la connexion MQTT
  if (!mqtt.connected()) {
    reconnectMQTT();
  }
  mqtt.loop();
  
  // Heartbeat périodique
  if (millis() - lastHeartbeat > 30000) {
    sendHeartbeat();
    lastHeartbeat = millis();
  }
  
  // Rendu à 20 FPS max
  if (millis() - lastRender > 10) {
    updateDisplay();
    lastRender = millis();
  }
  
  yield();
}

// ─── CONFIGURATION WIFI ────────────────────────────────────────────────────
void setupWiFi() {
  Serial.printf("📶 Connexion WiFi à '%s'...\n", WIFI_SSID);
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 30) {
    delay(500);
    Serial.print(".");
    attempts++;
  }
  
  if (WiFi.status() == WL_CONNECTED) {
    Serial.printf("\n✅ WiFi connecté - IP: %s\n", WiFi.localIP().toString().c_str());
    Serial.printf("   Signal: %d dBm\n", WiFi.RSSI());
  } else {
    Serial.println("\n❌ Échec connexion WiFi");
    ESP.restart();
  }
}

// ─── CONFIGURATION MQTT ────────────────────────────────────────────────────
void setupMQTT() {
  Serial.printf("🔗 Configuration MQTT: %s:%d\n", MQTT_BROKER, MQTT_PORT);
  
  // mqtt.setCACert(ca_cert);
  mqtt.setServer(MQTT_BROKER, MQTT_PORT);
  mqtt.setCallback(mqttCallback);
  mqtt.setBufferSize(MQTT_MAX_PACKET_SIZE); // Buffer élargi pour les grandes images
  
  reconnectMQTT();
}

void reconnectMQTT() {
  int attempts = 0;
  while (!mqtt.connected() && attempts < 5) {
    Serial.printf("🔄 Tentative MQTT %d...\n", attempts + 1);
    
    String clientId = "ESPEnfant" + String(CHILD_NUM) + "_" + String(random(0xffff), HEX);
    
    if (mqtt.connect(clientId.c_str())) {
      Serial.printf("✅ MQTT connecté avec ID: %s\n", clientId.c_str());
      
      // Subscription avec QoS 1 pour fiabilité
      if (mqtt.subscribe(TOPIC_CMD.c_str(), 1)) {
        Serial.printf("📺 Abonné au topic: %s\n", TOPIC_CMD.c_str());
      } else {
        Serial.println("❌ Échec subscription");
      }
      
      sendHeartbeat();
      return;
    }
    
    Serial.printf("❌ Échec MQTT (code %d), retry dans 2s\n", mqtt.state());
    delay(2000);
    attempts++;
  }
  
  if (!mqtt.connected()) {
    Serial.println("❌ Impossible de se connecter au MQTT, redémarrage...");
    delay(1000);
    ESP.restart();
  }
}

void sendHeartbeat() {
  if (!mqtt.connected()) return;
  
  DynamicJsonDocument doc(256);
  doc["child_id"] = CHILD_NUM;
  doc["status"] = "online";
  doc["ip"] = WiFi.localIP().toString();
  doc["rssi"] = WiFi.RSSI();
  doc["free_heap"] = ESP.getFreeHeap();
  doc["uptime"] = millis();
  
  String payload;
  serializeJson(doc, payload);
  
  // if (mqtt.publish(TOPIC_STATUS.c_str(), payload.c_str(), true)) {
    Serial.printf("💓 Heartbeat envoyé (heap: %d)\n", ESP.getFreeHeap());
  // }
}

// ─── CALLBACK MQTT ─────────────────────────────────────────────────────────
void mqttCallback(char* topic, byte* payload, unsigned int length) {
  Serial.printf("📨 Message reçu [%s] - %d bytes\n", topic, length);
  
  // Allouer buffer pour JSON avec marge de sécurité
  size_t jsonSize = length + 1024;
  DynamicJsonDocument* doc = new DynamicJsonDocument(jsonSize);
  
  if (!doc) {
    Serial.println("❌ Échec allocation JSON");
    return;
  }
  
  DeserializationError error = deserializeJson(*doc, payload, length);
  if (error) {
    Serial.printf("❌ Erreur JSON: %s\n", error.c_str());
    delete doc;
    return;
  }
  
  // Debug: afficher la commande reçue
  if (doc->containsKey("FLAG")) {
    Serial.printf("🎯 FLAG: %s\n", (*doc)["FLAG"].as<String>().c_str());
  }
  if (doc->containsKey("CMD")) {
    Serial.printf("🎯 CMD: %s\n", (*doc)["CMD"].as<String>().c_str());
  }
  
  // Traitement des commandes
  String flag = (*doc)["FLAG"] | "";
  String cmd = (*doc)["CMD"] | "";
  
  // Commandes avec FLAG
  if (flag == "VISUAL_PLAY") {
    handleVisualPlay(*doc);
  } else if (flag == "VISUAL_STOP") {
    handleVisualStop();
  } else if (flag == "QR_PLAY") {
    handleQRPlay(*doc);
  } else if (flag == "QR_STOP") {
    handleQRStop();
  }
  // Commandes avec CMD
  else if (cmd == "BRIGHTNESS") {
    handleBrightness(*doc);
  } else if (cmd == "POWER_OFF") {
    handlePowerOff();
  } else if (cmd == "CLEAR") {
    handleClear();
  } else if (cmd == "POWER_ON") {
    handlePowerOn();
  } else if (cmd == "ADS_PLAY") {
    handleAdsPlay(*doc);
  } else if (cmd == "ADS_STOP") {
    handleAdsStop();
  } else if (cmd == "LYRICS_PLAY") {
    handleLyricsPlay(*doc);
  } else if (cmd == "LYRICS_BLOCK") {
    handleLyricsBlock(*doc);
  } else if (cmd == "LYRICS_STOP") {
    handleLyricsStop();
  } else if (cmd == "CONFIG") {
    handleConfig(*doc);
  } else {
    Serial.printf("⚠️ Commande inconnue: FLAG='%s', CMD='%s'\n", flag.c_str(), cmd.c_str());
  }
  
  delete doc;
  Serial.printf("✅ Commande traitée (heap libre: %d)\n", ESP.getFreeHeap());
}

// ─── HANDLERS DES COMMANDES ────────────────────────────────────────────────

void handleVisualPlay(const JsonDocument& doc) {
  const char* b64 = doc["picture"];
  int width = doc["width"];
  int height = doc["height"];
  int segment = doc["segment"];
  
  Serial.printf("🖼️ VISUAL_PLAY: %dx%d, segment=%d, target=%d\n", width, height, segment, CHILD_NUM-1);
  
  // Vérifier si c'est pour nous
  if (segment != (CHILD_NUM - 1)) {
    Serial.println("⏭️ Pas pour moi, ignoré");
    return;
  }
  
  if (!b64 || width != SCREEN_WIDTH) {
    Serial.println("❌ Paramètres image invalides");
    return;
  }
  
  // Arrêter les autres animations
  lyrics.active = false;
  ads.active = false;
  waitingAnim.active = false;
  
  // Décoder et afficher
  memset(imageBuffer, 0, sizeof(imageBuffer));
  int decodedLen = base64Decode(b64, imageBuffer, sizeof(imageBuffer));
  
  if (decodedLen == SCREEN_WIDTH * SCREEN_HEIGHT * 3) {
    imageBufferValid = true;
    
    matrix.fillScreen(0);
    for (int i = 0; i < SCREEN_WIDTH * SCREEN_HEIGHT; i++) {
      int x = i % SCREEN_WIDTH;
      int y = i / SCREEN_WIDTH;
      uint32_t color = matrix.Color(
        imageBuffer[i*3], 
        imageBuffer[i*3+1], 
        imageBuffer[i*3+2]
      );
      matrix.drawPixel(x, y, color);
    }
    matrix.show();
    
    Serial.printf("✅ Image affichée (%d pixels)\n", SCREEN_WIDTH * SCREEN_HEIGHT);
  } else {
    Serial.printf("❌ Décodage échoué: %d bytes (attendu %d)\n", decodedLen, SCREEN_WIDTH * SCREEN_HEIGHT * 3);
  }
  verifConfig();
}

void handleVisualStop() {
  Serial.println("🛑 VISUAL_STOP");
  imageBufferValid = false;
  waitingAnim.active = true;
  matrix.fillScreen(0);
  matrix.show();
}

void handleQRPlay(const JsonDocument& doc) {
  int width = doc["width"];
  int height = doc["height"];
  int section = doc["section"];
  const char* b64 = doc["data"];
  
  Serial.printf("📱 QR_PLAY: %dx%d, section=%d, target=%d\n", width, height, section, CHILD_NUM-1);
  
  if (section != (CHILD_NUM - 1)) {
    Serial.println("⏭️ Pas pour moi, ignoré");
    return;
  }
  
  if (!b64 || width <= 0 || height <= 0) {
    Serial.println("❌ Paramètres QR invalides");
    return;
  }
  
  // Arrêter les autres animations
  lyrics.active = false;
  ads.active = false;
  imageBufferValid = false;
  waitingAnim.active = false;
  
  // Allouer buffer temporaire
  size_t bufferSize = width * height * 3;
  uint8_t* qrBuffer = (uint8_t*)malloc(bufferSize);
  if (!qrBuffer) {
    Serial.println("❌ Échec allocation QR buffer");
    return;
  }
  
  // Décoder
  int decoded = base64Decode(b64, qrBuffer, bufferSize);
  if (decoded != bufferSize) {
    Serial.printf("❌ Décodage QR échoué: %d/%d bytes\n", decoded, bufferSize);
    free(qrBuffer);
    return;
  }
  
  // Afficher
  matrix.fillScreen(0);
  for (int y = 0; y < min(SCREEN_HEIGHT, height); y++) {
    for (int x = 0; x < min(SCREEN_WIDTH, width); x++) {
      int idx = (y * width + x) * 3;
      uint8_t r = qrBuffer[idx];
      uint8_t g = qrBuffer[idx + 1];
      uint8_t b = qrBuffer[idx + 2];
      
      // Seuil pour QR: noir->blanc, blanc->noir
      int brightness = (r + g + b) / 3;
      uint32_t color;
      if (brightness < 128) {
        color = matrix.Color(QR_MODULE_BLACK_R, QR_MODULE_BLACK_G, QR_MODULE_BLACK_B);
      } else {
        color = matrix.Color(QR_MODULE_WHITE_R, QR_MODULE_WHITE_G, QR_MODULE_WHITE_B);
      }
      
      matrix.drawPixel(x, y, color);
    }
    yield();
  }
  matrix.show();
  
  free(qrBuffer);
  Serial.printf("✅ QR affiché (%dx%d)\n", width, height);
  verifConfig();
}

void handleQRStop() {
  Serial.println("🛑 QR_STOP");
  imageBufferValid = false;
  waitingAnim.active = true;
  matrix.fillScreen(0);
  matrix.show();
}

void handleLyricsPlay(const JsonDocument& doc) {
  Serial.println("🎵 LYRICS_PLAY");
  waitingAnim.active = false;
  matrix.fillScreen(0);
  
  lyrics.textColor = mapColor(doc["textColor"] | "white");
  lyrics.bgColor = mapColorBg(doc["backgroundColor"] | "black");
  lyrics.animation = doc["animation"] | "none";
  lyrics.active = true;
  // lyrics.text = "";
  
  // Arrêter les autres
  ads.active = false;
  imageBufferValid = false;
  
  // Init scroll
  if (lyrics.animation == "scroll_left") {
    lyrics.scrollX = SCREEN_WIDTH;
  } else if (lyrics.animation == "scroll_right") {
    lyrics.scrollX = -100; // Sera ajusté avec le texte
  }
  
  Serial.printf("✅ Lyrics activés: couleur=0x%04X, anim=%s\n", lyrics.textColor, lyrics.animation.c_str());
  verifConfig();
}

void handleLyricsBlock(const JsonDocument& doc) {
  if (!lyrics.active) return;
  
  lyrics.text = doc["text"] | "";
  Serial.printf("🎤 LYRICS_BLOCK: '%s'\n", lyrics.text.c_str());
  
  if (lyrics.animation == "none") {
    // Affichage statique immédiat
    matrix.fillScreen(lyrics.bgColor);
    matrix.setTextColor(lyrics.textColor);
    matrix.setTextSize(1);
    matrix.setTextWrap(true);

    int16_t x1,y1; uint16_t w,h;
    matrix.getTextBounds(lyrics.text,0,0,&x1,&y1,&w,&h);
    int16_t x = (SCREEN_WIDTH - w)/2;
    int16_t y = (SCREEN_HEIGHT - h)/2;
    matrix.setCursor(x, y);

    matrix.print(lyrics.text);
    matrix.show();

    verifConfig();
  }
  // Sinon, sera géré par updateDisplay()
  verifConfig();
}

void handleLyricsStop() {
  Serial.println("🛑 LYRICS_STOP");
  lyrics.active = false;
  waitingAnim.active = true;
  matrix.fillScreen(0);
  matrix.show();
}

void handleAdsPlay(const JsonDocument& doc) {
  Serial.println("📢 ADS_PLAY");
  waitingAnim.active = false;

  // stopWaitingAnimation();
  // startFeatureWithAnimation();
  
  ads.textColor = mapColor(doc["textColor"] | "white");
  ads.bgColor = mapColorBg(doc["bgColor"] | "black");
  ads.animation = doc["animation"] | "none";
  ads.content = doc["content"] | "";
  ads.speed = doc["speed"] | 1.0;
  ads.active = true;
  
  // Arrêter les autres
  lyrics.active = false;
  imageBufferValid = false;
  
  // Init scroll
  if (ads.animation == "scroll_left") {
    ads.scrollX = SCREEN_WIDTH;
    Serial.println("------ handleAdsPlay : scroll_left initialisé !");
  } else if (ads.animation == "scroll_right") {
    ads.scrollX = -(strlen(ads.content) * 6);
    Serial.println("------ handleAdsPlay : scroll_right initialisé !");
  } else if (ads.animation == "none") {
    // Si l'animation est Statique on centre le texte et on l'affiche
    matrix.fillScreen(ads.bgColor);
    matrix.setTextColor(ads.textColor);
    matrix.setTextWrap(true);
    matrix.setTextSize(1);

    int16_t x1,y1; uint16_t w,h;
    matrix.getTextBounds(ads.content,0,0,&x1,&y1,&w,&h);
    int16_t x = (SCREEN_WIDTH - w)/2;
    int16_t y = (SCREEN_HEIGHT - h)/2;
    matrix.setCursor(x, y);

    matrix.print(ads.content);
    matrix.show();
  }
  
  verifConfig();
  Serial.printf("✅ Ads activés: '%s', anim=%s\n", ads.content, ads.animation.c_str());
}

void handleAdsStop() {
  Serial.println("🛑 ADS_STOP");
  ads.active = false;
  waitingAnim.active = true;
  // renderDefault();
  // stopFeatureWithAnimation();
}

void handleBrightness(const JsonDocument& doc) {
  int brightness = constrain(doc["value"] | 50, 0, 255);
  matrix.setBrightness(brightness);
  matrix.show();
  Serial.printf("💡 Luminosité: %d\n", brightness);
}

void handlePowerOn(){
  Serial.println("🧹 POWER_ON");

  waitingAnim.active = true;
  // powerAnim.active = true;
  // fadeAnim.active = true;
  // fadeAnim.shouldStartWaiting = true;

  // renderDefault();
  // renderWaitingAnimation();
}

void handlePowerOff() {
  Serial.println("🧹 POWER_OFF");

  lyrics.active = false;
  ads.active = false;
  imageBufferValid = false;
  waitingAnim.active = false;
  powerAnim.active = false;
  fadeAnim.active = false;
  fadeAnim.shouldStartWaiting = false;

  matrix.fillScreen(0);
  matrix.show();
}

void handleClear() {
  Serial.println("🧹 CLEAR");

  lyrics.active = false;
  ads.active = false;
  imageBufferValid = false;
  waitingAnim.active = true;

  matrix.fillScreen(0);
  matrix.show();
}

void handleConfig(const JsonDocument& doc) {
  SCREEN_WIDTH = doc["screenWidth"];
  SCREEN_HEIGHT = doc["screenHeight"];

  isConfigured = true;

  saveConfig();

  verifConfig();
}

void verifConfig() {
  screenMatrixCount = SCREEN_WIDTH / MATRIX_SIZE;
  realMatrixCount   = MAT_W / MATRIX_SIZE;

  if (realMatrixCount > screenMatrixCount) {
    int overflowCount = realMatrixCount - screenMatrixCount;
    
    Serial.print("[Config] ");
    Serial.print(overflowCount);
    Serial.println(" matrices non configurées détectées.");

    // Affiche une croix rouge clignotante sur les matrices non prises en compte
      renderMatrixOut(screenMatrixCount, overflowCount);
  } else {
    Serial.println("[Config] Toutes les matrices sont prises en compte dans la configuration.");
  }
}

// ------ Save Config ------
void saveConfig() {
  EEPROM.write(ADDR_CONFIGURED, 1);
  EEPROM.write(ADDR_SCREEN_WIDTH, SCREEN_WIDTH);
  EEPROM.write(ADDR_SCREEN_HEIGHT, SCREEN_HEIGHT);
  EEPROM.commit();
  
  Serial.println("[Config] Configuration sauvegardée en EEPROM");
}

// ------ Load Config ------
bool loadConfig() {
  bool configured = EEPROM.read(ADDR_CONFIGURED) == 1;
  
  if (configured) {
    SCREEN_WIDTH  = EEPROM.read(ADDR_SCREEN_WIDTH);
    SCREEN_HEIGHT  = EEPROM.read(ADDR_SCREEN_HEIGHT);

    isConfigured = true;
    
    Serial.println("[Config] Configuration chargée depuis EEPROM :");
    Serial.print("[Config] - Width Configuré : ");
    Serial.println(SCREEN_WIDTH);
    Serial.print("[Config] - Height Configuré : ");
    Serial.println(SCREEN_HEIGHT);
  } else {
    Serial.println("[Config] Aucune configuration trouvée en EEPROM");
    // Configuration par défaut (32x32 logique)
    SCREEN_WIDTH = 48;
    SCREEN_HEIGHT = 16;
    isConfigured = false;
  }
  
  return configured;
}

// ─── RENDU ─────────────────────────────────────────────────────────────────

void updateDisplay() {
  // updateFadeAnimation();
  
  if (powerAnim.active) {
    renderPowerAnimation();
  } else if (imageBufferValid) {
    // L'image statique est déjà affichée, rien à faire
    refreshVisualIfNeeded();
  } else if (lyrics.active && lyrics.animation != "none") {
    renderLyrics();
  } else if (ads.active && ads.animation != "none") {
    renderAds();
  } else if (waitingAnim.active) {
    renderDefault();
  } else {
    // Fallback au comportement par défaut
    // renderDefault();
    // refreshMatrixOutIfNeeded();
    return;
  }
}

// void renderLyrics() {
//   if (lyrics.text.isEmpty()) return;

//   matrix.fillScreen(lyrics.bgColor);
//   matrix.setTextColor(lyrics.textColor);
//   matrix.setTextSize(1);
//   matrix.setTextWrap(false);
//   matrix.setCursor(lyrics.scrollX, 4);
//   matrix.print(lyrics.text);
//   matrix.show();
  
//   int lyrics_length = -(lyrics.text.length() * 6);
//   Serial.printf("lyrics_length = %d\n", lyrics_length);
//   // Animation
//   if (lyrics.animation == "scroll_left") {
//     lyrics.scrollX--;
//     if (lyrics.scrollX < lyrics_length) {
//       lyrics.scrollX = SCREEN_WIDTH;
//       Serial.println("------ renderLyrics : on affiche le texte défilant à GAUCHE !");
//     }
//   } else if (lyrics.animation == "scroll_right") {
//     lyrics.scrollX++;
//     if (lyrics.scrollX > SCREEN_WIDTH) {
//       lyrics.scrollX = -(lyrics.text.length() * 6);
//       Serial.println("------ renderLyrics : on affiche le texte défilant à DROITE !");
//     }
//   }

//   verifConfig();
// }

void renderLyrics() {
  if (lyrics.text.isEmpty()) return;

  int speed = 2; // Vitesse fixe comme dans l'original
  int lyrics_length = (lyrics.text.length() * 6);
  
  if (lyrics.animation == "scroll_left") {
    Serial.println("------ renderLyrics : on affiche le texte défilant à GAUCHE !");
    
    // Condition élargie pour permettre l'affichage
    if (lyrics.scrollX > -lyrics_length && lyrics.scrollX < SCREEN_WIDTH) {
      const int CHAR_W = 6;
      int len = lyrics.text.length();
      int textStart = lyrics.scrollX;
      int textEnd = textStart + lyrics_length;
      
      if (textEnd > SCREEN_WIDTH) {
        // Calculer combien de caractères on peut afficher
        int visibleWidth = SCREEN_WIDTH - textStart;
        int visibleChars = visibleWidth / CHAR_W;
        
        if (visibleChars > 0 && visibleChars <= len) {
          String tempText = lyrics.text.substring(0, visibleChars);
          matrix.fillScreen(lyrics.bgColor);
          matrix.setTextColor(lyrics.textColor);
          matrix.setTextSize(1);
          matrix.setTextWrap(false);
          matrix.setCursor(lyrics.scrollX, 4);
          matrix.print(tempText);
        }
      } else {
        // Le texte tient entièrement dans la zone visible
        matrix.fillScreen(lyrics.bgColor);
        matrix.setTextColor(lyrics.textColor);
        matrix.setTextSize(1);
        matrix.setTextWrap(false);
        matrix.setCursor(lyrics.scrollX, 4);
        matrix.print(lyrics.text);
      }
    }
    
    // Défilement vers la gauche
    lyrics.scrollX -= speed;
    
    // Réinitialisation pour scroll_left
    if (lyrics.scrollX <= -lyrics_length) {
      lyrics.scrollX = SCREEN_WIDTH;
    }
    
  } else if (lyrics.animation == "scroll_right") {
    Serial.println("------ renderLyrics : on affiche le texte défilant à DROITE !");
    
    // Condition - on affiche tant que le texte n'est pas complètement sorti à droite
    if (lyrics.scrollX < SCREEN_WIDTH + lyrics_length) {
      const int CHAR_W = 6;
      int len = lyrics.text.length();
      int textStart = lyrics.scrollX;
      int textEnd = textStart + lyrics_length;
      
      // Arrêter de dessiner avant que la première lettre n'atteigne complètement le bord
      if (textStart <= SCREEN_WIDTH - 6) {  // -6 pour la largeur d'un caractère
        if (textEnd > SCREEN_WIDTH) {
          // Le texte dépasse à droite - calculer combien de caractères on peut afficher
          int visibleWidth = SCREEN_WIDTH - textStart;
          int visibleChars = visibleWidth / CHAR_W;
          
          if (visibleChars > 0 && visibleChars <= len) {
            String tempText = lyrics.text.substring(0, visibleChars);
            matrix.fillScreen(lyrics.bgColor);
            matrix.setTextColor(lyrics.textColor);
            matrix.setTextSize(1);
            matrix.setTextWrap(false);
            matrix.setCursor(lyrics.scrollX, 4);
            matrix.print(tempText);
          }
        } else {
          // Le texte tient entièrement (même si une partie est à gauche en négatif)
          matrix.fillScreen(lyrics.bgColor);
          matrix.setTextColor(lyrics.textColor);
          matrix.setTextSize(1);
          matrix.setTextWrap(false);
          matrix.setCursor(lyrics.scrollX, 4);
          matrix.print(lyrics.text);
        }
      } else {
        // Le texte est complètement sorti à droite - effacer l'écran
        matrix.fillScreen(lyrics.bgColor);
      }
    }
    
    // Défilement vers la droite
    lyrics.scrollX += speed;
    
    // Réinitialisation pour scroll_right - attendre que tout le texte soit sorti
    if (lyrics.scrollX >= SCREEN_WIDTH + lyrics_length) {
      lyrics.scrollX = -lyrics_length;
    }
  }

  matrix.show();
  verifConfig();
  // refreshMatrixOutIfNeeded();
}

void renderAds() {
  // --------- Fonctionnel V1 : pas de prise en compte écran config ----------
  // matrix.fillScreen(ads.bgColor);
  // matrix.setTextColor(ads.textColor);
  // matrix.setTextSize(1);
  // matrix.setTextWrap(false);
  // matrix.setCursor(ads.scrollX, 4);
  // matrix.print(ads.content);
  // matrix.show();
  
  // int ads_length = -(ads.content.length() * 6);
  // Serial.printf("ads_length = %d\n", ads_length);
  // // Animation avec vitesse
  // if (ads.animation != "none") {
  //   int step = 1;
  //   if (ads.animation == "scroll_left") {
  //     ads.scrollX -= step;
  //     if (ads.scrollX < ads_length) {
  //       ads.scrollX = SCREEN_WIDTH;
  //       Serial.println("------ renderAds : on affiche le texte défilant !");
  //     }
  //   } else if (ads.animation == "scroll_right") {
  //     ads.scrollX += step;
  //     if (ads.scrollX > SCREEN_WIDTH) {
  //       ads.scrollX = -(ads.content.length() * 6);
  //     }
  //   }
  //   if (ads.speed > 0) delay(int(10.0/(ads.speed*2)));
  // }

  // --------- Fonctionnel V2 : prise en compte écran config mais uniquement 'scroll_left' ----------
  // Serial.println("On fait défile vers la GAUCHE ------------------");
  // int speed = ads.speed > 0 ? ads.speed/2 : 1;
  // int ads_length = (strlen(ads.content) * 6);

  // if (ads.scrollX > (-ads_length) && ads.scrollX < SCREEN_WIDTH) {

  //   const int CHAR_W = 6;  // largeur d'un caractère en pixels (avec espacement)
  //   int len = strlen(ads.content);
  //   int textStart = ads.scrollX;
  //   int textEnd = textStart + ads_length;
    
  //   // Si le texte dépasse la zone configurée à droite, on le tronque
  //   if (textEnd > SCREEN_WIDTH) {
  //     // Calculer combien de caractères on peut afficher
  //     int visibleWidth = SCREEN_WIDTH - textStart;
  //     int visibleChars = visibleWidth / CHAR_W;
      
  //     if (visibleChars > 0 && visibleChars <= len) {
  //       // Créer une sous-chaîne avec seulement les caractères visibles
  //       char tempText[32];
  //       strncpy(tempText, ads.content, visibleChars);
  //       tempText[visibleChars] = '\0';
  //       matrix.fillScreen(ads.bgColor);
  //       matrix.setTextColor(ads.textColor);
  //       matrix.setTextSize(1);
  //       matrix.setTextWrap(false);
  //       matrix.setCursor(ads.scrollX, 4);
  //       matrix.print(tempText);
  //     }
  //   } else {
  //     // Le texte tient entièrement dans la zone configurée
  //     matrix.fillScreen(ads.bgColor);
  //     matrix.setTextColor(ads.textColor);
  //     matrix.setTextSize(1);
  //     matrix.setTextWrap(false);
  //     matrix.setCursor(ads.scrollX, 4);
  //     matrix.print(ads.content);
  //   }
  // }
  // ads.scrollX -= speed;
  // // ads.scrollX--;
  // if (ads.scrollX <= -ads_length) {
  //   ads.scrollX = SCREEN_WIDTH;
  // }
  // if (ads.speed > 0) speed = ads.speed/2;

  // verifConfig();

  // --------- Fonctionnel V3 : prise en compte écran config ----------
  int speed = ads.speed > 1 ? ads.speed/2 : 1;
  int ads_length = (strlen(ads.content) * 6);
  
  if (ads.animation == "scroll_left") {
    Serial.println("On fait défiler vers la GAUCHE ------------------");
    
    // Condition élargie pour permettre l'affichage
    if (ads.scrollX > -ads_length && ads.scrollX < SCREEN_WIDTH) {
      const int CHAR_W = 6;
      int len = strlen(ads.content);
      int textStart = ads.scrollX;
      int textEnd = textStart + ads_length;
      
      // Effacer l'écran et configurer l'affichage
      
      if (textEnd > SCREEN_WIDTH) {
        // Calculer combien de caractères on peut afficher
        int visibleWidth = SCREEN_WIDTH - textStart;
        int visibleChars = visibleWidth / CHAR_W;
        
        if (visibleChars > 0 && visibleChars <= len) {
          char tempText[64]; // Augmenté la taille du buffer
          strncpy(tempText, ads.content, visibleChars);
          tempText[visibleChars] = '\0';
          matrix.fillScreen(ads.bgColor);
          matrix.setTextColor(ads.textColor);
          matrix.setTextSize(1);
          matrix.setTextWrap(false);
          matrix.setCursor(ads.scrollX, 4);
          matrix.print(tempText);
        }
      } else {
        // Le texte tient entièrement dans la zone visible
        matrix.fillScreen(ads.bgColor);
        matrix.setTextColor(ads.textColor);
        matrix.setTextSize(1);
        matrix.setTextWrap(false);
        matrix.setCursor(ads.scrollX, 4);
        matrix.print(ads.content);
      }
    }
    
    // Défilement vers la gauche
    ads.scrollX -= speed;
    
    // Réinitialisation pour scroll_left
    if (ads.scrollX <= -ads_length) {
      ads.scrollX = SCREEN_WIDTH;
    }
    
  } else if (ads.animation == "scroll_right") {
    Serial.println("On fait défiler vers la DROITE ------------------");
    
    // Condition simple - on affiche tant que le texte n'est pas complètement sorti à droite
    if (ads.scrollX < SCREEN_WIDTH) {
      const int CHAR_W = 6;
      int len = strlen(ads.content);
      int textStart = ads.scrollX;
      int textEnd = textStart + ads_length;
      
      if (textStart <= SCREEN_WIDTH - 6) {
        if (textEnd > SCREEN_WIDTH) {
          // Le texte dépasse à droite - calculer combien de caractères on peut afficher
          int visibleWidth = SCREEN_WIDTH - textStart;
          int visibleChars = visibleWidth / CHAR_W;
          
          if (visibleChars > 0 && visibleChars <= len) {
            char tempText[64];
            strncpy(tempText, ads.content, visibleChars);
            tempText[visibleChars] = '\0';
            matrix.fillScreen(ads.bgColor);
            matrix.setTextColor(ads.textColor);
            matrix.setTextSize(1);
            matrix.setTextWrap(false);
            matrix.setCursor(ads.scrollX, 4);
            matrix.print(tempText);
          }
        } else {
          // Le texte tient entièrement (même si une partie est à gauche en négatif)
          matrix.fillScreen(ads.bgColor);
          matrix.setTextColor(ads.textColor);
          matrix.setTextSize(1);
          matrix.setTextWrap(false);
          matrix.setCursor(ads.scrollX, 4);
          matrix.print(ads.content);
        }
      } else {
        // Le texte est complètement sorti à droite - effacer l'écran
        matrix.fillScreen(ads.bgColor);
      }
    }
    
    // Défilement vers la droite
    ads.scrollX += speed;
    
    // Réinitialisation pour scroll_right - recommencer depuis la gauche
    if (ads.scrollX >= SCREEN_WIDTH) {
      ads.scrollX = -ads_length;
    }
  }

  verifConfig();
}

void renderDefault() {
  // ----- Affichage Statique -----
  // matrix.fillScreen(0);
  // matrix.setTextColor(matrix.Color(255,255,255));
  // matrix.setTextSize(1);
  // matrix.setCursor(2, 4);
  // matrix.print("ESP" + String(CHILD_NUM));
  // matrix.show();

  // ---- Affichage Dynamique -----
  if (waitingAnim.active && !lyrics.active && 
      !ads.active && !imageBufferValid) {
    renderWaitingAnimation();
  }
}

void renderMatrixOut(int startMatrix, int matrixCount) {
  uint32_t color = matrix.Color(255, 0, 0);

  for (int m = 0; m < matrixCount; m++) {
    int x_offset = (startMatrix + m) * MATRIX_SIZE;

    // Nettoyage de la zone cible
    for (int x = x_offset; x < x_offset + MATRIX_SIZE; x++) {
      for (int y = 0; y < MATRIX_SIZE; y++) {
        matrix.drawPixel(x, y, 0); // Éteint les pixels
      }
    }

    // Dessine la croix rouge
    for (int i = 0; i < MATRIX_SIZE; i++) {
      matrix.drawPixel(x_offset + i, i, color);                         // Diagonale "/"
      matrix.drawPixel(x_offset + i, MATRIX_SIZE - 1 - i, color);      // Diagonale "\"
    }
  }

  matrix.show();
  // delay(1000);
}

void refreshMatrixOutIfNeeded() {
  // On ne fait rien si pas encore assez de temps écoulé
  if (millis() - lastRefresh < REFRESH_INTERVAL) return;

  lastRefresh = millis();

  // Recalcule le nombre réel de matrices connectées
  verifConfig();
}

void refreshVisualIfNeeded() {
  if (millis() - lastRefresh < REFRESH_INTERVAL) return;

  lastRefresh = millis();

  // Recalcule le nombre réel de matrices connectées
  return;
}

// ─── UTILITAIRES ───────────────────────────────────────────────────────────

int base64Decode(const char* input, uint8_t* output, size_t maxOutputSize) {
  if (!input || !output) return -1;
  
  const char* chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
  size_t in_len = strlen(input);
  size_t i = 0, o = 0;
  
  while (i + 3 < in_len && o + 2 < maxOutputSize) {
    int vals[4];
    bool valid = true;
    
    for (int j = 0; j < 4; j++) {
      char c = input[i + j];
      if (c == '=') {
        vals[j] = 0;
      } else {
        const char* pos = strchr(chars, c);
        if (pos) {
          vals[j] = pos - chars;
        } else {
          valid = false;
          break;
        }
      }
    }
    
    if (!valid) {
      i++;
      continue;
    }
    
    uint32_t combined = (vals[0] << 18) | (vals[1] << 12) | (vals[2] << 6) | vals[3];
    
    output[o++] = (combined >> 16) & 0xFF;
    if (input[i + 2] != '=' && o < maxOutputSize) {
      output[o++] = (combined >> 8) & 0xFF;
    }
    if (input[i + 3] != '=' && o < maxOutputSize) {
      output[o++] = combined & 0xFF;
    }
    
    i += 4;
    
    if (i % 100 == 0) yield(); // Éviter le watchdog
  }
  
  return (int)o;
}

uint16_t mapColor(const String& name) {
  String c = name;
  c.toLowerCase();
  if (c == "white") return matrix.Color(255,255,255);
  if (c == "red") return matrix.Color(255,0,0);
  if (c == "green") return matrix.Color(0,255,0);
  if (c == "blue") return matrix.Color(0,0,255);
  if (c == "yellow") return matrix.Color(255,255,0);
  if (c == "cyan") return matrix.Color(0,255,255);
  if (c == "magenta") return matrix.Color(255,0,255);
  if (c == "black" || c == "none") return matrix.Color(0,0,0);
  return matrix.Color(255,255,255);
}

uint16_t mapColorBg(const String& name) {
  String c = name;
  c.toLowerCase();
  if (c == "white") return matrix.Color(127,127,127);
  if (c == "red") return matrix.Color(127,0,0);
  if (c == "green") return matrix.Color(0,127,0);
  if (c == "blue") return matrix.Color(0,0,127);
  if (c == "yellow") return matrix.Color(127,127,0);
  if (c == "cyan") return matrix.Color(0,127,127);
  if (c == "magenta") return matrix.Color(127,0,127);
  if (c == "black" || c == "none") return matrix.Color(0,0,0);
  return matrix.Color(127,127,127);
}