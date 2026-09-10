#include <WiFi.h>
#include <HTTPClient.h>

// --- Wi-Fi Credentials ---
const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";

// Server endpoint (Replace with your computer's local IP running app.py)
const char* serverUrl = "http://192.168.1.100:5000/api/sensor-data";

// --- Hardware Identification ---
const char* SENSOR_ID = "M001";
const char* MOUNTAIN_ID = "MT001";

// --- Sensor Analog Pins ---
const int SOIL_PIN = 34; // Soil Moisture Sensor (Analog)
const int RAIN_PIN = 35; // Rain Sensor (Analog)

// --- Indicator & Buzzer Pins ---
const int PIN_LED_GREEN  = 18;
const int PIN_LED_ORANGE = 19;
const int PIN_LED_RED    = 21;
const int PIN_BUZZER     = 22;

// --- Calibration Thresholds ---
// Rain detection threshold: above 5 mm is considered raining
const float RAIN_THRESHOLD_MM = 5.0; 

// Soil risk threshold: above 70% moisture represents elevated hazard risk
const float SOIL_RISK_THRESHOLD = 70.0; 

// Soil ADC calibration constants (ESP32 ADC is 0 - 4095)
// Dry air gives higher ADC values; submerged in water gives lower ADC values
const int SOIL_DRY_AIR = 3200; 
const int SOIL_WET_WATER = 1300;

// Rain ADC calibration constants
const int RAIN_DRY = 4095;
const int RAIN_WET = 1200;

void setup() {
  Serial.begin(115200);
  delay(1000);

  // Initialize output pins
  pinMode(PIN_LED_GREEN, OUTPUT);
  pinMode(PIN_LED_ORANGE, OUTPUT);
  pinMode(PIN_LED_RED, OUTPUT);
  pinMode(PIN_BUZZER, OUTPUT);

  // Default state: all off during boot
  digitalWrite(PIN_LED_GREEN, LOW);
  digitalWrite(PIN_LED_ORANGE, LOW);
  digitalWrite(PIN_LED_RED, LOW);
  digitalWrite(PIN_BUZZER, LOW);

  Serial.println("\n--- MountainWatch ESP32 Telemetry & Alert Node ---");
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi Connected! Local IP: ");
  Serial.println(WiFi.localIP());
}

void loop() {
  // 1. Read Raw Analog Values
  int rawMoisture = analogRead(SOIL_PIN);
  int rawRain = analogRead(RAIN_PIN);

  // 2. Convert Raw Readings to Scaled Metrics
  float moisturePct = map(rawMoisture, SOIL_DRY_AIR, SOIL_WET_WATER, 0, 100);
  moisturePct = constrain(moisturePct, 0.0, 100.0);

  float rainfall_mm = map(rawRain, RAIN_DRY, RAIN_WET, 0, 60);
  rainfall_mm = constrain(rainfall_mm, 0.0, 100.0);

  // 3. Condition Evaluation
  bool isRaining = (rainfall_mm >= RAIN_THRESHOLD_MM);
  bool hasRisk   = (moisturePct >= SOIL_RISK_THRESHOLD);

  Serial.printf("\nTelemetry -> Moisture: %.1f%% | Rain: %.1f mm\n", moisturePct, rainfall_mm);

  // 4. Actuator Logic:
  // Case A: Rain AND Risk -> RED LED + BUZZER
  // Case B: Rain BUT NO Risk -> ORANGE LED
  // Case C: No Rain AND NO Risk -> GREEN LED
  if (isRaining && hasRisk) {
    Serial.println("STATUS: [CRITICAL] Rain + High Risk detected!");
    digitalWrite(PIN_LED_GREEN, LOW);
    digitalWrite(PIN_LED_ORANGE, LOW);
    digitalWrite(PIN_LED_RED, HIGH);
    digitalWrite(PIN_BUZZER, HIGH);
  }
  else if (isRaining && !hasRisk) {
    Serial.println("STATUS: [WATCH] Rain detected, soil moisture within safe limits.");
    digitalWrite(PIN_LED_GREEN, LOW);
    digitalWrite(PIN_LED_ORANGE, HIGH);
    digitalWrite(PIN_LED_RED, LOW);
    digitalWrite(PIN_BUZZER, LOW);
  }
  else {
    Serial.println("STATUS: [NORMAL] No rain, nominal soil moisture.");
    digitalWrite(PIN_LED_GREEN, HIGH);
    digitalWrite(PIN_LED_ORANGE, LOW);
    digitalWrite(PIN_LED_RED, LOW);
    digitalWrite(PIN_BUZZER, LOW);
  }

  // 5. Send Telemetry to Flask Server via Wi-Fi
  if (WiFi.status() == WL_CONNECTED) {
    String jsonPayload = "{";
    jsonPayload += "\"sensor_id\":\"" + String(SENSOR_ID) + "\",";
    jsonPayload += "\"mountain_id\":\"" + String(MOUNTAIN_ID) + "\",";
    jsonPayload += "\"moisture\":" + String(moisturePct, 1) + ",";
    jsonPayload += "\"rainfall\":" + String(rainfall_mm, 1);
    jsonPayload += "}";

    HTTPClient http;
    http.begin(serverUrl);
    http.addHeader("Content-Type", "application/json");

    int httpCode = http.POST(jsonPayload);
    if (httpCode > 0) {
      String response = http.getString();
      Serial.printf("Server Response [%d]: %s\n", httpCode, response.c_str());
    } else {
      Serial.printf("HTTP Failed: %s\n", http.errorToString(httpCode).c_str());
    }
    http.end();
  } else {
    Serial.println("Warning: Wi-Fi disconnected. Reconnecting...");
  }

  // Polling interval (10 seconds)
  delay(10000);
}