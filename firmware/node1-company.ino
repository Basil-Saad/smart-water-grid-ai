// AquaGrid - Node 1 (Company side)

// Libraries 
#include <WiFi.h>
#include <WiFiClientSecure.h>
#define ENABLE_DATABASE // Use database features from FirebaseClient
#include <FirebaseClient.h>

// Pin definitions
#define FLOW_PIN 27
#define TRIG_PIN 5
#define ECHO_PIN 18
#define TDS_PIN 35
#define VALVE_PIN 26
#define PUMP_PIN 25

// WiFi credentials
const char* WIFI_SSID = "WiFiNetwork";
const char* WIFI_PASSWORD = "hope1234";

// Firebase credentials
#define DATABASE_URL "https://aquagrid-39dc4-default-rtdb.europe-west1.firebasedatabase.app"

// Firebase objects
WiFiClientSecure ssl;
using AsyncClient = AsyncClientClass;
AsyncClient asyncClient(ssl);
NoAuth noAuth;
FirebaseApp app;
RealtimeDatabase Database;
AsyncResult dbResult;

// sensor variables
volatile int pulseCount = 0;
float flowRate = 0; // Flow sensor
float consumption = 0;
float level = 0; // level sensor
float tds = 0; // tds sensor 

// Tank calibration table
const int TABLE_SIZE = 7;
float distTable[TABLE_SIZE] = {24.06, 21.97, 18.66, 16.07, 14.06, 11.71, 6.76};
float volTable[TABLE_SIZE]  = {0.0,   0.5,   1.0,   1.5,   2.0,   2.5,   3.0};
const float TANK_CAPACITY = 3.0;

// Timing
unsigned long lastTime = 0;
unsigned long hourStartTime = 0;

// Zero flow detection
int zeroFlowCount = 0;

// Interrupt function - runs when pulse detected
void IRAM_ATTR pulseCounter() {
  pulseCount++;
}

void setup() {
  // Start serial communication for debugging
  Serial.begin(115200);
  
  // Configure ADC
  analogReadResolution(12);
  analogSetAttenuation(ADC_11db);
  
  // Set pin modes
  pinMode(FLOW_PIN, INPUT);
  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);
  pinMode(VALVE_PIN, OUTPUT);
  pinMode(PUMP_PIN, OUTPUT);
  
  // Start with actuators OFF
  digitalWrite(VALVE_PIN, LOW);
  digitalWrite(PUMP_PIN, LOW);
  
  Serial.println("Node 1 starting...");

  // Connect to WiFi
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  Serial.print("Connecting to WiFi");
  
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  
  Serial.println();
  Serial.println("WiFi connected!");
  WiFi.setSleep(false);  // Disable WiFi sleep
  Serial.print("IP address: ");
  Serial.println(WiFi.localIP());

  // Initialize Firebase
  Serial.println("Connecting to Firebase...");
  
  ssl.setInsecure();
  
  initializeApp(asyncClient, app, getAuth(noAuth));
  
  app.getApp<RealtimeDatabase>(Database);
  Database.url(DATABASE_URL);
  
  Serial.println("Firebase connected!");

  // Initialize hour timer
  hourStartTime = millis();

  // Attach interrupt to flow sensor
  attachInterrupt(digitalPinToInterrupt(FLOW_PIN), pulseCounter, RISING);
}

void loop() {
  // Process Firebase tasks
  app.loop();
  
  // Maintain Firebase authentication
  if (app.ready()) {
    // Firebase is ready
  } else {
    Serial.println("Firebase not ready, waiting...");
    delay(100);
    return;  // Skip this loop iteration
  }
  
  // Check WiFi connection
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("WiFi disconnected! Reconnecting...");
    WiFi.disconnect();
    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
    
    while (WiFi.status() != WL_CONNECTED) {
      delay(500);
      Serial.print(".");
    }
    Serial.println();
    Serial.println("WiFi reconnected!");
  }
  // Run every 1 second
  if (millis() - lastTime >= 1000) {
    
    // ----- FLOW SENSOR -----
    detachInterrupt(digitalPinToInterrupt(FLOW_PIN)); // Disable interrupt while calculating
    flowRate = pulseCount / 3.25; // Calculate flow rate (L/min)
    float litersThisSecond = pulseCount / 225.0;
    pulseCount = 0; // Reset counter
    attachInterrupt(digitalPinToInterrupt(FLOW_PIN), pulseCounter, RISING); // Re-enable interrupt
    
    // ----- ACCUMULATION WITH 5-SECOND CHECK -----
    if (flowRate > 0) {
      zeroFlowCount = 0;
    } else {
      zeroFlowCount++;
    }
    
    // Only accumulate if flow was active in last 5 seconds
    if (zeroFlowCount < 5 && litersThisSecond > 0.032){
      consumption += 0.032;
    }
    else if (zeroFlowCount < 5) {
      consumption += 0.37*(litersThisSecond);
    }
    
    // ----- HOURLY RESET -----
    if (millis() - hourStartTime >= 3600000) {
      consumption = 0;
      hourStartTime = millis();
      Serial.println("Hour passed - consumption reset!");
    }

    // ----- ULTRASONIC SENSOR -----
    float readings[10];
    int validCount = 0;
    
    for (int i = 0; i < 10; i++) {
      digitalWrite(TRIG_PIN, LOW);
      delayMicroseconds(3);
      digitalWrite(TRIG_PIN, HIGH);
      delayMicroseconds(10);
      digitalWrite(TRIG_PIN, LOW);
      
      long duration = pulseIn(ECHO_PIN, HIGH, 30000);
      if (duration > 0) {
        float d = (duration * 0.0343) / 2.0;
        if (d > 2 && d < 50) {
          readings[validCount] = d;
          validCount++;
        }
      }
      delay(50);
    }
    
    // Calculate level using median
    if (validCount >= 3) {
      // Sort readings
      for (int i = 0; i < validCount - 1; i++) {
        for (int j = 0; j < validCount - i - 1; j++) {
          if (readings[j] > readings[j + 1]) {
            float temp = readings[j];
            readings[j] = readings[j + 1];
            readings[j + 1] = temp;
          }
        }
      }
      
      // Get median
      float distance = readings[validCount / 2];
      
      // Interpolate from table
      float volume = 0;
      if (distance >= distTable[0]) {
        volume = 0;
      } else if (distance <= distTable[TABLE_SIZE - 1]) {
        volume = TANK_CAPACITY;
      } else {
        for (int i = 0; i < TABLE_SIZE - 1; i++) {
          if (distance <= distTable[i] && distance >= distTable[i + 1]) {
            volume = volTable[i] + (distTable[i] - distance) * (volTable[i + 1] - volTable[i]) / (distTable[i] - distTable[i + 1]);
            break;
          }
        }
      }
      
      level = (volume / TANK_CAPACITY) * 100.0;
    }
    
    // ----- TDS SENSOR -----
    int tdsReadings[20];
    for (int i = 0; i < 20; i++) {
      tdsReadings[i] = analogRead(TDS_PIN);
      delay(2);
    }
    
    // Sort to find median (simple bubble sort)
    for (int i = 0; i < 19; i++) {
      for (int j = 0; j < 19 - i; j++) {
        if (tdsReadings[j] > tdsReadings[j + 1]) {
          int temp = tdsReadings[j];
          tdsReadings[j] = tdsReadings[j + 1];
          tdsReadings[j + 1] = temp;
        }
      }
    }
    
    // Get median (middle value)
    int tdsAdc = tdsReadings[10];
    float tdsVoltage = (tdsAdc / 4095.0) * 3.3;
    tds = (133.42 * tdsVoltage * tdsVoltage * tdsVoltage 
         - 255.86 * tdsVoltage * tdsVoltage 
         + 857.39 * tdsVoltage) * 0.5;
    
    // Update last time
    lastTime = millis();
    
    // ----- PRINT FOR DEBUGGING -----
    Serial.print("consumption: ");
    Serial.print(consumption);
    Serial.print(" L, Level: ");
    Serial.print(level);
    Serial.print(" %, TDS: ");
    Serial.print(tds);
    Serial.println(" ppm");

    // ----- SEND TO FIREBASE -----
    Database.set<float>(asyncClient, "/nodes/node1/sensors/consumption", consumption);
    Database.set<float>(asyncClient, "/nodes/node1/sensors/level", level);
    Database.set<float>(asyncClient, "/nodes/node1/sensors/tds", tds);

    // ----- READ COMMANDS FROM FIREBASE -----
    bool valveState = Database.get<bool>(asyncClient, "/nodes/node1/actuators/valve");
    bool pumpState = Database.get<bool>(asyncClient, "/nodes/node1/actuators/pump");
    
    // ----- CONTROL ACTUATORS -----
    if (valveState) {
      digitalWrite(VALVE_PIN, HIGH);
      Serial.println("Valve: OPEN");
    } else {
      digitalWrite(VALVE_PIN, LOW);
      Serial.println("Valve: CLOSED");
    }
    
    if (pumpState) {
      digitalWrite(PUMP_PIN, HIGH);
      Serial.println("Pump: ON");
    } else {
      digitalWrite(PUMP_PIN, LOW);
      Serial.println("Pump: OFF");
    }

    // ----- CHECK RESET COMMAND -----
    bool resetCmd = Database.get<bool>(asyncClient, "/nodes/node1/commands/resetConsumption");
    if (resetCmd) {
      consumption = 0;
      hourStartTime = millis();
      Serial.println("Consumption reset by dashboard!");
      Database.set<bool>(asyncClient, "/nodes/node1/commands/resetConsumption", false);
    }
  }
}