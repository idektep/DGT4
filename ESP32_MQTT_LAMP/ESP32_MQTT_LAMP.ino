#include <WiFi.h>
#include <PubSubClient.h>

// =====================
// CONFIG
// =====================
const char* ssid = "bank daysun";
const char* password = "37511900";

const char* mqtt_server = "broker.emqx.io";
const int   mqtt_port   = 1883;

// Topics
const char* TOPIC_CAM   = "dgt/smartcam/status";
const char* TOPIC_CMD   = "dgt/light/cmd";
const char* TOPIC_STAT  = "dgt/light/status";

// GPIO
const int PIN_LIGHT  = 2;
const int PIN_SWITCH = 15;

// =====================
WiFiClient espClient;
PubSubClient client(espClient);

bool lightState = false;
bool lastSwitch = HIGH;

// =====================
void publishLight() {
  if (lightState) {
    client.publish(TOPIC_STAT, "on");
    Serial.println("[MQTT] Publish: on");
  } else {
    client.publish(TOPIC_STAT, "off");
    Serial.println("[MQTT] Publish: off");
  }
}

// =====================
void mqttCallback(char* topic, byte* payload, unsigned int length) {
  String msg;
  for (int i = 0; i < length; i++) msg += (char)payload[i];

  Serial.printf("[MQTT] %s → %s\n", topic, msg.c_str());

  if (String(topic) == TOPIC_CAM && msg == "detect") {
    lightState = true;
    digitalWrite(PIN_LIGHT, HIGH);
    publishLight();
  }

  if (String(topic) == TOPIC_CMD && msg == "toggle") {
    lightState = !lightState;
    digitalWrite(PIN_LIGHT, lightState ? HIGH : LOW);
    publishLight();
  }
}

// =====================
void setup_wifi() {
  Serial.print("[WiFi] Connecting");
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500); Serial.print(".");
  }
  Serial.println("\n[WiFi] Connected");
}

// =====================
void reconnect() {
  while (!client.connected()) {
    Serial.print("[MQTT] Connecting...");
    if (client.connect("esp32_rtu")) {
      Serial.println("OK");
      client.subscribe(TOPIC_CAM);
      client.subscribe(TOPIC_CMD);
    } else {
      Serial.println("FAIL");
      delay(2000);
    }
  }
}

// =====================
void setup() {
  Serial.begin(115200);
  pinMode(PIN_LIGHT, OUTPUT);
  pinMode(PIN_SWITCH, INPUT_PULLUP);
  digitalWrite(PIN_LIGHT, LOW);

  setup_wifi();
  client.setServer(mqtt_server, mqtt_port);
  client.setCallback(mqttCallback);
}

// =====================
void loop() {
  if (!client.connected()) reconnect();
  client.loop();

  bool sw = digitalRead(PIN_SWITCH);
  if (sw == LOW && lastSwitch == HIGH) {
    lightState = !lightState;
    digitalWrite(PIN_LIGHT, lightState ? HIGH : LOW);
    publishLight();
    delay(300);
  }
  lastSwitch = sw;
}
