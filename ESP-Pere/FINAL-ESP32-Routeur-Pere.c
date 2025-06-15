#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include <Adafruit_GFX.h>
#include <EEPROM.h>
#include <algorithm>

// ─────── CONFIGURATION GÉNÉRALE ─────────────────────────────────────────────
const char* AP_SSID      = "MonReseauESP";
const char* AP_PASS      = "ouiouioui";
IPAddress local_IP(192, 168, 1, 1);
IPAddress gateway_IP(192, 168, 1, 1);
IPAddress subnet_mask(255, 255, 255, 0);

// MQTT
const char* MQTT_BROKER_IP   = "192.168.1.10";
const uint16_t MQTT_BROKER_PORT = 1883;
const char* MQTT_TOPIC_PERE  = "esp/pere/commande";
#define MQTT_MAX_PACKET_SIZE 21000 

// ─────── CONFIGURATION EEPROM ────────────────────────────────────────────────
#define ADDR_CONFIGURED    0
#define ADDR_SCREEN_COUNT  1
#define ADDR_MATRIX_COUNT  2
#define ADDR_SHAPE         3
#define EEPROM_SIZE        16

// ─────── ENFANTS ─────────────────────────────────────────────────────────────
#define MAX_CHILDREN 3
const char* CHILD_TOPICS[MAX_CHILDREN]       = { "esp/enfant1/command", "esp/enfant2/command", "esp/enfant3/command" };
const char* enfantsDisplayTopics[MAX_CHILDREN] = { "esp/enfant1/display", "esp/enfant2/display", "esp/enfant3/display" };
const char* enfantsCommandTopics[] = {
  "esp/enfant1/command",
  "esp/enfant2/command",
  "esp/enfant3/command"
};
const int nombreEnfants = sizeof(enfantsDisplayTopics)/sizeof(enfantsDisplayTopics[0]);

struct ChildESP {
  String topic;
  bool   connected;
  unsigned long lastSeen;
};
ChildESP children[MAX_CHILDREN];
int numChildren = MAX_CHILDREN;

// écran distribué (Visual + QR)
#define SCREEN_WIDTH      64
#define CHILD_HEIGHT      16
#define TOTAL_SCREEN_HEIGHT 16

// ─────── BUFFERS ─────────────────────────────────────────────────────────────
WiFiClient wifiClient;
PubSubClient mqttClient(wifiClient);
uint8_t imageBuffer[15360] __attribute__((aligned(4))); // 48×48×3
bool imageBufferValid = false;

// ─────── VARIABLES LYRICS/ADS ─────────────────────────────────────────────────
bool   isConfigured = false;
int    screenCount  = 1;
int    matrixCount  = 4;
String screenShape  = "Square";

struct AdsParams { 
  String textColor; 
  String bgColor; 
  String animation;
  String font; 
  float speed; 
  String content; 
};

struct LyricsParams { 
  String textColor; 
  String backgroundColor; 
  String font; 
  String animation; 
  bool isPlaying; 
};

LyricsParams currentLyricsStyle;

// PROTOTYPES
void sendConfig();

// ─────── FONCTIONS BASE64 CUSTOM (PRÉSERVÉES) ────────────────────────────────
static const int8_t b64index[256] = {
  -1,-1,-1,-1,-1,-1,-1,-1,  // 0–7
  -1,-1,-1,-1,-1,-1,-1,-1,  // 8–15
  -1,-1,-1,-1,-1,-1,-1,-1,  // 16–23
  -1,-1,-1,-1,-1,-1,-1,-1,  // 24–31
  -1,-1,-1,-1,-1,-1,-1,-1,  // 32–39
  -1,-1,-1,62,-1,-1,-1,63,  // 40–47  '+'=43 → 62 ; '/'=47 → 63
  52,53,54,55,56,57,58,59,  // 48–55  '0'–'7'
  60,61,-1,-1,-1,-1,-1,-1,  // 56–63  '8'–'9'
  -1, 0, 1, 2, 3, 4, 5, 6,  // 64–71  'A'–'G'
   7, 8, 9,10,11,12,13,14,  // 72–79  'H'–'O'
  15,16,17,18,19,20,21,22,  // 80–87  'P'–'W'
  23,24,25,-1,-1,-1,-1,-1,  // 88–95  'X'–'Z'
  -1,26,27,28,29,30,31,32,  // 96–103 'a'–'g'
  33,34,35,36,37,38,39,40,  // 104–111 'h'–'o'
  41,42,43,44,45,46,47,48,  // 112–119 'p'–'w'
  49,50,51,-1,-1,-1,-1,-1,  // 120–127 'x'–'z'
  -1,-1,-1,-1,-1,-1,-1,-1,  // 128–135
  -1,-1,-1,-1,-1,-1,-1,-1,  // 136–143
  -1,-1,-1,-1,-1,-1,-1,-1,  // 144–151
  -1,-1,-1,-1,-1,-1,-1,-1,  // 152–159
  -1,-1,-1,-1,-1,-1,-1,-1,  // 160–167
  -1,-1,-1,-1,-1,-1,-1,-1,  // 168–175
  -1,-1,-1,-1,-1,-1,-1,-1,  // 176–183
  -1,-1,-1,-1,-1,-1,-1,-1,  // 184–191
  -1,-1,-1,-1,-1,-1,-1,-1,  // 192–199
  -1,-1,-1,-1,-1,-1,-1,-1,  // 200–207
  -1,-1,-1,-1,-1,-1,-1,-1,  // 208–215
  -1,-1,-1,-1,-1,-1,-1,-1,  // 216–223
  -1,-1,-1,-1,-1,-1,-1,-1,  // 224–231
  -1,-1,-1,-1,-1,-1,-1,-1,  // 232–239
  -1,-1,-1,-1,-1,-1,-1,-1,  // 240–247
  -1,-1,-1,-1,-1,-1,-1,-1   // 248–255
};

String base64Encode(uint8_t* data, size_t length) {
  const char base64_chars[] = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
  String encoded;
  encoded.reserve((length * 4 / 3) + 4);
  size_t i = 0; uint8_t char_array_3[3], char_array_4[4];
  while (i < length) {
    char_array_3[0] = data[i++];
    char_array_3[1] = (i < length) ? data[i++] : 0;
    char_array_3[2] = (i < length) ? data[i++] : 0;
    char_array_4[0] = (char_array_3[0] & 0xfc) >> 2;
    char_array_4[1] = ((char_array_3[0] & 0x03) << 4) | ((char_array_3[1] & 0xf0) >> 4);
    char_array_4[2] = ((char_array_3[1] & 0x0f) << 2) | ((char_array_3[2] & 0xc0) >> 6);
    char_array_4[3] = char_array_3[2] & 0x3f;
    for (int j = 0; j < 4; j++) encoded += base64_chars[char_array_4[j]];
  }
  size_t mod = length % 3;
  if (mod == 1) { encoded[encoded.length()-2] = '='; encoded[encoded.length()-1] = '='; }
  else if (mod == 2) { encoded[encoded.length()-1] = '='; }
  return encoded;
}

int base64Decode(const char* input, uint8_t* output, size_t maxOutputSize) {
  Serial.println("Décodage du Base64");
  if (!input || !output) return -1;
  size_t in_len = strlen(input), i=0, o=0; int8_t vals[4]; int val_count=0;
  size_t estimated_output = (in_len * 3)/4;
  if (estimated_output > maxOutputSize) return -1;
  while (i < in_len && o < maxOutputSize-3) {
    char c = input[i++];
    if      (c=='=') vals[val_count++]=-2;
    else if (c>=0 && c<256 && b64index[(uint8_t)c]>=0) vals[val_count++]=b64index[(uint8_t)c];
    if (val_count==4) {
      uint32_t triple = ((uint32_t)vals[0]<<18)|((uint32_t)vals[1]<<12);
      if (vals[2]>=0) { triple|=((uint32_t)vals[2]<<6);
        if (vals[3]>=0) { triple|=vals[3]; output[o++]=(triple>>16)&0xFF; output[o++]=(triple>>8)&0xFF; output[o++]=triple&0xFF; }
        else if (vals[3]==-2) { output[o++]=(triple>>16)&0xFF; output[o++]=(triple>>8)&0xFF; }
      } else if (vals[2]==-2) { output[o++]=(triple>>16)&0xFF; }
      val_count=0;
    }
  }
  return o;
}

// ─────── FONCTIONS DISTRIBUTION ET UTILITAIRES ────────────────────────────────
void initializeChildren() {
  for (int i=0;i<MAX_CHILDREN;i++) {
    children[i].topic = String(CHILD_TOPICS[i]); children[i].connected=false; children[i].lastSeen=0;
  }
}

void sendToChild(int childIndex, uint8_t* imageData,int imageWidth,int imageHeight,const char* flagType) { 
  if (childIndex >= numChildren || childIndex < 0) {
    Serial.printf("[ERROR] Index enfant invalide: %d\n", childIndex);
    return;
  }
  
  const char* childTopic = children[childIndex].topic.c_str();
  Serial.printf("[CHILD%d] Préparation données pour %s\n", childIndex + 1, childTopic);
  
  // Calculer la zone à extraire pour cet enfant
  int startY = childIndex * CHILD_HEIGHT;
  int endY = min(startY + CHILD_HEIGHT, imageHeight);
  int actualHeight = endY - startY;
  
  if (actualHeight <= 0) {
    Serial.printf("[CHILD%d] Aucune donnée à envoyer (startY=%d, imageHeight=%d)\n", 
                  childIndex + 1, startY, imageHeight);
    return;
  }
  
  // Buffer pour cette section
  int sectionWidth = min(SCREEN_WIDTH, imageWidth);
  size_t sectionSize = sectionWidth * actualHeight * 3;
  uint8_t* sectionBuf = (uint8_t*)malloc(sectionSize);
  
  if (!sectionBuf) {
    Serial.printf("[ERROR] Impossible d'allouer %u bytes pour enfant %d\n", sectionSize, childIndex + 1);
    return;
  }
  
  // Extraire les pixels de cette section avec redimensionnement si nécessaire
  for (int y = 0; y < actualHeight; y++) {
    for (int x = 0; x < sectionWidth; x++) {
      // Coordonnées source avec redimensionnement
      int srcY = startY + y;
      int srcX = x;
      
      // S'assurer qu'on reste dans les limites
      if (srcY >= imageHeight) srcY = imageHeight - 1;
      if (srcX >= imageWidth) srcX = imageWidth - 1;
      
      int srcIndex = (srcY * imageWidth + srcX) * 3;
      int dstIndex = (y * sectionWidth + x) * 3;
      
      if (srcIndex + 2 < imageWidth * imageHeight * 3 && dstIndex + 2 < sectionSize) {
        sectionBuf[dstIndex] = imageData[srcIndex];         // R
        sectionBuf[dstIndex + 1] = imageData[srcIndex + 1]; // G  
        sectionBuf[dstIndex + 2] = imageData[srcIndex + 2]; // B
      } else {
        // Pixel noir si hors limites
        sectionBuf[dstIndex] = 0;
        sectionBuf[dstIndex + 1] = 0;
        sectionBuf[dstIndex + 2] = 0;
      }
    }
  }
  
  // Encoder en base64
  String base64Data = base64Encode(sectionBuf, sectionSize);
  free(sectionBuf);
  
  if (base64Data.length() == 0) {
    Serial.printf("[ERROR] Échec encodage Base64 pour enfant %d\n", childIndex + 1);
    return;
  }
  
  // Créer le message JSON unifié
  DynamicJsonDocument doc(base64Data.length() + 1000);
  doc["FLAG"] = flagType;
  
  if (strcmp(flagType, "QR_PLAY") == 0) {
    // Format QR Code
    doc["width"] = sectionWidth;
    doc["height"] = actualHeight;
    doc["data"] = base64Data;
    doc["section"] = childIndex;
  } else {
    // Format Visual (VISUAL_PLAY)
    doc["picture"] = base64Data;
    doc["width"] = sectionWidth;
    doc["height"] = actualHeight;
    doc["segment"] = childIndex;
  }
  
  doc["timestamp"] = millis();
  
  String jsonMessage;
  serializeJson(doc, jsonMessage);
  
  Serial.printf("[CHILD%d] Envoi %u bytes (JSON: %u bytes, Base64: %u bytes)\n", 
                childIndex + 1, sectionSize, jsonMessage.length(), base64Data.length());
  
  // Envoyer via MQTT
  bool sent = mqttClient.publish(childTopic, jsonMessage.c_str());
  if (sent) {
    Serial.printf("[CHILD%d] Section %d envoyée avec succès\n", childIndex + 1, childIndex);
  } else {
    Serial.printf("[ERROR] Échec envoi section à enfant %d\n", childIndex + 1);
  }
  
  doc.clear();
  yield();
}

void distributeToChildren(uint8_t* imageData,int imageWidth,int imageHeight,const char* flagType) { 
  Serial.printf("[DISTRIBUTE] Distribution %s de %dx%d vers %d enfants\n",
                flagType, imageWidth, imageHeight, numChildren);
  for (int i = 0; i < numChildren; i++) {
    sendToChild(i, imageData, imageWidth, imageHeight, flagType);
    delay(100);
  }
  Serial.printf("[DISTRIBUTE] Distribution %s terminée\n", flagType);
}

void stopAllChildren() { 
  Serial.println("🛑 Envoi commande STOP à tous les enfants...");
  
  DynamicJsonDocument stopDoc(200);
  stopDoc["CMD"] = "CLEAR";
  stopDoc["timestamp"] = millis();
  
  String stopMessage;
  serializeJson(stopDoc, stopMessage);
  
  for (int i = 0; i < numChildren; i++) {
    bool sent = mqttClient.publish(children[i].topic.c_str(), stopMessage.c_str());
    Serial.printf("%s STOP envoyé à ESP%d\n", sent ? "✅" : "❌", i + 1);
    delay(20);
  }
  
  stopDoc.clear();
}

void distributeContentAdaptive(const String& content,const String& commandType, AdsParams* adsParams = nullptr) {
  // Calcul adaptatif du nombre de caractères par enfant selon la configuration
  int maxCharsPerChild = calculateMaxCharsPerChild();
  
  Serial.print("[Distribution] Contenu : '");
  Serial.print(content);
  Serial.print("' - ");
  Serial.print(maxCharsPerChild);
  Serial.println(" chars max par enfant");
  
  for (int i = 0; i < nombreEnfants; i++) {
    int start = i * maxCharsPerChild;
    int end   = std::min(start + maxCharsPerChild, (int)content.length());
    String part = (start < content.length()) ? content.substring(start, end) : "";
    part.trim();
    
    StaticJsonDocument<512> cmd;
    
    if (commandType == "ADS_PLAY" && adsParams != nullptr) {
      cmd["CMD"]       = "ADS_PLAY";
      cmd["textColor"] = adsParams->textColor;
      cmd["bgColor"]   = adsParams->bgColor;
      cmd["font"]      = adsParams->font;
      cmd["animation"] = adsParams->animation;
      cmd["speed"]     = adsParams->speed;
      cmd["content"]   = part;
    }
    else if (commandType == "LYRICS_BLOCK") {
      cmd["CMD"]             = "LYRICS_BLOCK";
      cmd["text"]            = part;
      cmd["textColor"]       = currentLyricsStyle.textColor;
      cmd["backgroundColor"] = currentLyricsStyle.backgroundColor;
      cmd["font"]            = currentLyricsStyle.font;
      cmd["animation"]       = currentLyricsStyle.animation;
    }
    else if (commandType == "LYRICS_PLAY") {
      // envoi du style de lyrics aux enfants
      cmd["CMD"]             = "LYRICS_PLAY";
      cmd["textColor"]       = currentLyricsStyle.textColor;
      cmd["backgroundColor"] = currentLyricsStyle.backgroundColor;
      cmd["font"]            = currentLyricsStyle.font;
      cmd["animation"]       = currentLyricsStyle.animation;
     }
    
    sendCommandToChildren(i, cmd);
    
    Serial.print("[Distribution] Enfant ");
    Serial.print(i + 1);
    Serial.print(" : '");
    Serial.print(part);
    Serial.println("'");

    Serial.print(" CMD=");
    Serial.println(commandType);
  }
}

// Fonctions LYRICS/ADS/CONFIG
void handleConfig(JsonDocument& doc) {
  int sc = doc["screenCount"].as<int>();
  int mc = doc["matrixCount"].as<int>();
  String sh = doc["screenShape"].as<String>();

  int mw = 0;
  int mh = 0;
  int child_count = 0;
  
  Serial.print("[Config] Demande de configuration : ");
  Serial.print("screenCount=");
  Serial.print(sc);
  Serial.print(", matrixCount=");
  Serial.print(mc);
  Serial.print(", screenShape=");
  Serial.println(sh);
  
  // Validation de la configuration
  if (sh == "Square" && mc >= 4) {
    if (sc == 1 && (mc == 4 || mc == 9)) { // Limites de sécurité
      screenCount = sc;
      matrixCount = mc;
      screenShape = sh;
      isConfigured = true;
      saveConfig();

      mw = (mc == 4) ? 32 : 48;
      mh = (mc == 4) ? 32 : 48;
      child_count = (mc == 4) ? 2 : 3;
      sendConfig(child_count, mw, mh);
      
      Serial.println("[Config] Configuration acceptée et sauvegardée !");
      Serial.print("[Config] Configuration active : ");
      Serial.print(screenCount);
      Serial.print(" écrans, ");
      Serial.print(matrixCount);
      Serial.print(" matrices, forme ");
      Serial.println(screenShape);
    } else {
      Serial.println("[Config] Configuration refusée - limites dépassées");
    }
  } else if (sh == "Line") {
    if (sc == 1 && mc >= 2 && mc <= 6) {
      screenCount = sc;
      matrixCount = mc;
      screenShape = sh;
      isConfigured = true;
      saveConfig();

      mw = (mc == 2) ? 32 :
           ((mc == 3) ? 48 :
           ((mc == 4) ? 64 :
           ((mc == 5) ? 80 : 
           ((mc == 6) ? 96 : 32))));
      mh = 16;
      child_count = 1;
      sendConfig(child_count, mw, mh);
      
      Serial.println("[Config] Configuration acceptée et sauvegardée !");
      Serial.print("[Config] Configuration active : ");
      Serial.print(screenCount);
      Serial.print(" écrans, ");
      Serial.print(matrixCount);
      Serial.print(" matrices, forme ");
      Serial.println(screenShape);
    } else {
      Serial.println("[Config] Configuration refusée - limites dépassées");
    }
  } else if (sh == "Horizontal Rectangle" || sh == "Vertical Rectangle") {
    if (sc == 1 && mc == 6) {
      screenCount = sc;
      matrixCount = mc;
      screenShape = sh;
      isConfigured = true;
      saveConfig();
      
      mw = (sh == "Horizontal Rectangle") ? 48 : 32;
      mh = (sh == "Horizontal Rectangle") ? 32 : 48;
      child_count = (sh == "Horizontal Rectangle") ? 2 : 3;
      sendConfig(child_count, mw, mh);
      
      Serial.println("[Config] Configuration acceptée et sauvegardée !");
      Serial.print("[Config] Configuration active : ");
      Serial.print(screenCount);
      Serial.print(" écrans, ");
      Serial.print(matrixCount);
      Serial.print(" matrices, forme ");
      Serial.println(screenShape);
    } else {
      Serial.println("[Config] Configuration refusée - limites dépassées");
    }
  } else {
    Serial.println("[Config] Configuration refusée - paramètres invalides");
  }
}

void handlePower(const String& flag) {
    StaticJsonDocument<100> cmd;
  cmd["CMD"] = (flag == "POWER_ON") ? "POWER_ON" : "POWER_OFF";
  
  Serial.print("[Power] Commande : ");
  Serial.println(flag);
  
  broadcastCommand(cmd);
}

void handleBrightness(JsonDocument& doc) {
    int brightnessValue = doc["value"].as<int>();
  
  StaticJsonDocument<100> cmd;
  cmd["CMD"] = "BRIGHTNESS";
  cmd["value"] = brightnessValue;
  
  Serial.print("[Brightness] Réglage luminosité : ");
  Serial.println(brightnessValue);
  
  broadcastCommand(cmd);
}

void handleAdsPlay(JsonDocument& doc) {
  Serial.println("[ADS] Début de diffusion publicitaire");
  
  AdsParams params;
  params.textColor = doc["textColor"]       | "white";
  params.bgColor   = doc["backgroundColor"] | "none";
  params.font      = doc["font"]            | "Arial";
  params.animation = doc["animation"]       | "none";
  params.speed     = doc["speed"]           | 1;
  params.content   = doc["content"].as<String>();
  
  distributeContentAdaptive(params.content, "ADS_PLAY", &params);
}

void handleAdsStop() {
  Serial.println("[ADS] Arrêt de la diffusion publicitaire");

  StaticJsonDocument<100> cmd;
  cmd["CMD"] = "ADS_STOP";
  broadcastCommand(cmd);
}

void handleLyricsPlay(JsonDocument& doc) {
  Serial.println("[LYRICS] Configuration du style des paroles");
  
  currentLyricsStyle.textColor       = doc["textColor"]       | "white";
  currentLyricsStyle.backgroundColor = doc["backgroundColor"] | "none";
  currentLyricsStyle.font            = doc["font"]            | "Arial";
  currentLyricsStyle.animation       = doc["animation"]       | "none";
  currentLyricsStyle.isPlaying       = true;
  
  Serial.println("[LYRICS] Style configuré pour les paroles");
  distributeContentAdaptive("", "LYRICS_PLAY");
}

void handleLyricsBlock(JsonDocument& doc) {
  if (!currentLyricsStyle.isPlaying) {
    Serial.println("[LYRICS] Paroles non activées - bloc ignoré");
    return;
  }
  
  String text = doc["text"].as<String>();
  Serial.print("[LYRICS] Affichage du bloc : ");
  Serial.println(text);
  
  distributeContentAdaptive(text, "LYRICS_BLOCK", nullptr);
}

void handleLyricsStop() {
  Serial.println("[LYRICS] Arrêt de l'affichage des paroles");
  
  currentLyricsStyle.isPlaying = false;
  
  StaticJsonDocument<200> cmd;
  cmd["CMD"] = "LYRICS_STOP";
  broadcastCommand(cmd);
}

int calculateMaxCharsPerChild() {
  // Calcul basé sur la configuration d'écran
  // Logique d'écran 32x32 par défaut = ~5-7 caractères par ligne
  // Pour une matrice 16x16, on peut afficher environ 2-3 caractères par ligne
  
  int baseChars = 5; // Valeur de base conservative
  
  if (matrixCount == 4 && screenShape == "Square") {
    // Configuration 2x2 (32x32 logique) Idéal : 5
    baseChars = 5;
  }
  else if (matrixCount == 6 && screenShape == "Horizontal Rectangle") {
    // Configuration 3x2 (48x32 logique) Idéal : 8
    baseChars = 8;
  }
  else if (matrixCount == 6 && screenShape == "Vertical Rectangle") {
    // Configuration 2x3 (32x48 logique) Idéal : 5
    baseChars = 5;
  }
  else if (matrixCount == 9 && screenShape == "Square") {
    // Configuration 3x3 (48x48 logique) Idéal : 8
    baseChars = 8;
  } else if (screenShape == "Line") {
    switch (matrixCount) {
      case 2:
        baseChars = 5;
        break;
      case 3:
        baseChars = 8;
        break;
      case 4:
        baseChars = 11;
        break;
      case 5:
        baseChars = 14;
        break;
      case 6:
        baseChars = 17;
        break;
      default:
        baseChars = 8;
        break;
    }
  }
  
  return baseChars;
}

void distribuerMessage(const String& msg) {
  // Distribution simple pour les messages sans FLAG
  // int maxChars = calculateMaxCharsPerChild();
  
  // for (int i = 0; i < nombreEnfants; i++) {
  //   int start = i * maxChars;
  //   int end   = std::min(start + maxChars, (int)msg.length());
  //   String part = (start < msg.length()) ? msg.substring(start, end) : "";
  //   part.trim();
    
  //   if (part.length() > 0) {
  //     mqttClient.publish(enfantsDisplayTopics[i], part.c_str());
  //   }
  // }
}

void broadcastCommand(JsonDocument& cmd) {
  for (int i = 0; i < nombreEnfants; i++) {
    sendCommandToChildren(i, cmd);
  }
}
void sendCommandToChildren(int idx, JsonDocument& cmd) {
  if (idx >= 0 && idx < nombreEnfants) {
    char buffer[512];
    serializeJson(cmd, buffer);
    mqttClient.publish(enfantsCommandTopics[idx], buffer);
  }
}
uint16_t mapColor(const String& colorName) {
  String col = colorName;
  col.toLowerCase();
  
  if (col == "white")   return 0xFFFF;
  if (col == "red")     return 0xF800;
  if (col == "green")   return 0x07E0;
  if (col == "blue")    return 0x001F;
  if (col == "yellow")  return 0xFFE0;
  if (col == "cyan")    return 0x07FF;
  if (col == "magenta" || col == "purple" || col == "pink") return 0xF81F;
  if (col == "orange")  return 0xFD20;
  if (col == "black" || col == "none") return 0x0000;
  
  // Couleur par défaut
  return 0xFFFF; // Blanc
}

void saveConfig() {
  EEPROM.begin(EEPROM_SIZE);
  EEPROM.write(ADDR_CONFIGURED, 1);
  EEPROM.write(ADDR_SCREEN_COUNT, screenCount);
  EEPROM.write(ADDR_MATRIX_COUNT, matrixCount);
  if (screenShape == "Square"){
    EEPROM.write(ADDR_SHAPE, 'S');
  } else if (screenShape == "Line"){
    EEPROM.write(ADDR_SHAPE, 'L');
  } else if (screenShape == "Horizontal Rectangle"){
    EEPROM.write(ADDR_SHAPE, 'HR');
  } else if (screenShape == "Vertical Rectangle"){
    EEPROM.write(ADDR_SHAPE, 'VR');
  } else {
    Serial.println("[Config] : Erreur lors de l'écriture dans la mémoire, config incorrecte !");
    EEPROM.end();
    return;
  }
  EEPROM.write(ADDR_SHAPE, (screenShape == "Square") ? 'S' : 'R');
  EEPROM.commit();
  EEPROM.end();
  
  Serial.println("[Config] Configuration sauvegardée en EEPROM");
}

void sendConfig(int child_count, int mw, int mh) {
  // Création du document JSON
  StaticJsonDocument<256> configOk;

  // Remplir les champs requis
  configOk["CMD"] = "CONFIG";
  configOk["screenWidth"] = mw;
  configOk["screenHeight"] = 16;

  StaticJsonDocument<256> configNotOk;

  // Remplir les champs requis
  configNotOk["CMD"] = "CONFIG";
  configNotOk["screenWidth"] = 0;
  configNotOk["screenHeight"] = 0;

  // Envoi via la fonction de diffusion MQTT
  // broadcastCommand(configDoc);
  if (child_count == 1) {
    // OK : On envoie la config adaptée
    for (int i = 0; i < child_count; i++) {
      sendCommandToChildren(i, configOk);
    }

    // NOT OK : On envoie la config de "pas de matrices" aux autres ESP
    for (int i = 1; i < MAX_CHILDREN; i++) {
      sendCommandToChildren(i, configNotOk);
    }
  } else if (child_count == 2) {
    // OK : On envoie la config adaptée
    for (int i = 0; i < child_count; i++) {
      sendCommandToChildren(i, configOk);
    }

    // NOT OK : On envoie la config de "pas de matrices" aux autres ESP
    for (int i = 2; i < MAX_CHILDREN; i++) {
      sendCommandToChildren(i, configNotOk);
    }
  } else if (child_count == 3) {
    // OK : On envoie la config adaptée
    for (int i = 0; i < child_count; i++) {
      sendCommandToChildren(i, configOk);
    }
  }

  Serial.println("[MQTT] Configuration envoyée via MQTT :");
  serializeJsonPretty(configOk, Serial);
  serializeJsonPretty(configNotOk, Serial);
  Serial.println(); // Nouvelle ligne propre
}

bool loadConfig() {
  EEPROM.begin(EEPROM_SIZE);
  bool configured = EEPROM.read(ADDR_CONFIGURED);
  
  if (configured) {
    screenCount  = EEPROM.read(ADDR_SCREEN_COUNT);
    matrixCount  = EEPROM.read(ADDR_MATRIX_COUNT);
    char shapeChar = EEPROM.read(ADDR_SHAPE);

    if (shapeChar == 'S') {
      screenShape = "Square";
    } else if (shapeChar == 'L') {
      screenShape = "Line";
    } else if (shapeChar == 'HR') {
      screenShape = "Horizontal Rectangle";
    } else if (shapeChar == 'VR') {
      screenShape = "Vertical Rectangle";
    } else {
      Serial.println("[Config] Configuration NON chargée depuis EEPROM...");
      EEPROM.end();
      return false;
    }

      isConfigured = true;
      
      Serial.println("[Config] Configuration chargée depuis EEPROM :");
      Serial.print("[Config] - Écrans : ");
      Serial.println(screenCount);
      Serial.print("[Config] - Matrices : ");
      Serial.println(matrixCount);
      Serial.print("[Config] - Forme : ");
      Serial.println(screenShape);
  } else {
    Serial.println("[Config] Aucune configuration trouvée en EEPROM");
    // Configuration par défaut (32x32 logique)
    screenCount = 2;
    matrixCount = 4;
    screenShape = "Square";
    isConfigured = false;
  }
  
  EEPROM.end();
  return configured;
}

void mqttCallback(char* topic, byte* payload, unsigned int length) {
  // Combiner logique ESP32-EPIC1-2 et ESP32-EPIC3-4
  String msg;
  for(unsigned int i=0;i<length;i++) msg+=(char)payload[i];
  DynamicJsonDocument doc(20000);
  if(deserializeJson(doc,msg)) return;

  String flag = doc.containsKey("FLAG") ? doc["FLAG"].as<String>() : String();

  if(flag=="QR_PLAY"||flag=="VISUAL_PLAY") {
    // traitement image + distribution
    const char* b64 = (flag=="QR_PLAY"?doc["data"]:doc["picture"]);
    int w=doc["width"], h=doc["height"];

    if (!b64) {
      Serial.println("Erreur: données base64 manquantes");
      return;
    }
    
    Serial.printf("Décodage base64: longueur=%d, w=%d, h=%d\n", strlen(b64), w, h);
    
    int len = base64Decode(b64,imageBuffer,sizeof(imageBuffer));
    Serial.printf("Résultat décodage: %d bytes\n", len);
    
    if(len > 0) {
      distributeToChildren(imageBuffer,w,h,flag.c_str());
      Serial.println("QRCode ou Visuel distribué aux enfants");
    } else {
      Serial.println("Erreur lors du décodage base64");
    }

  } else if(flag=="VISUAL_STOP" || flag=="QR_STOP") { stopAllChildren(); }
  else if(flag=="CONFIG") { handleConfig(doc); }
  else if(flag=="POWER_ON"||flag=="POWER_OFF") { handlePower(flag); }
  else if(flag=="BRIGHTNESS") { handleBrightness(doc); }
  else if(flag=="ADS_PLAY") { handleAdsPlay(doc); }
  else if(flag=="ADS_STOP") { handleAdsStop(); }
  else if(flag=="LYRICS_PLAY") { handleLyricsPlay(doc); }
  else if(flag=="LYRICS_BLOCK") { handleLyricsBlock(doc); }
  else if(flag=="LYRICS_STOP") { handleLyricsStop(); }
  else { 
    return;
  }
}

void reconnectMQTT() {
  mqttClient.setBufferSize(MQTT_MAX_PACKET_SIZE);
  while(!mqttClient.connected()) {
    if(mqttClient.connect("ESP32Master")) {
      mqttClient.subscribe(MQTT_TOPIC_PERE);
    } else delay(2000);
  }
}

void setup() {
  Serial.begin(115200);
  WiFi.softAPConfig(local_IP,gateway_IP,subnet_mask);
  WiFi.softAP(AP_SSID,AP_PASS, 1, 0, 8);
  initializeChildren();
  mqttClient.setServer(MQTT_BROKER_IP, MQTT_BROKER_PORT);
  mqttClient.setCallback(mqttCallback);
  EEPROM.begin(EEPROM_SIZE);
  loadConfig();
}

void loop() {
  if(!mqttClient.connected()) reconnectMQTT();
  mqttClient.loop();
  delay(10);
}
