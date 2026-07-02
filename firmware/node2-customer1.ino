// AquaGrid - Node 2 (Costumer 1)

// Libraries 
#include <WiFi.h>
#include <WiFiClientSecure.h>
#define ENABLE_DATABASE // Use database features from FirebaseClient
#include <FirebaseClient.h>

// Pin definitions
#define FLOW_PIN 27
#define VALVE_PIN 26

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
  pinMode(VALVE_PIN, OUTPUT);
  
  // Start with actuators OFF
  digitalWrite(VALVE_PIN, LOW);
  
  Serial.println("Node 2 starting...");

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
      consumption += 0.02;
    }
    else if (zeroFlowCount < 5) {
      consumption += 0.59*(litersThisSecond);
    }
    
    // ----- HOURLY RESET -----
    if (millis() - hourStartTime >= 3600000) {
      consumption = 0;
      hourStartTime = millis();
      Serial.println("Hour passed - consumption reset!");
    }

    // Update last time
    lastTime = millis();
      
    // ----- PRINT FOR DEBUGGING -----
    Serial.print("consumption: ");
    Serial.print(consumption);
    Serial.println(" L");

    // ----- SEND TO FIREBASE -----
    Database.set<float>(asyncClient, "/nodes/node2/sensors/consumption", consumption);

    // ----- READ COMMANDS FROM FIREBASE -----
    bool valveState = Database.get<bool>(asyncClient, "/nodes/node2/actuators/valve");
    
    // ----- CONTROL ACTUATORS -----
    if (valveState) {
      digitalWrite(VALVE_PIN, HIGH);
      Serial.println("Valve: OPEN");
    } else {
      digitalWrite(VALVE_PIN, LOW);
      Serial.println("Valve: CLOSED");
    }

    // ----- CHECK RESET COMMAND -----
    bool resetCmd = Database.get<bool>(asyncClient, "/nodes/node2/commands/resetConsumption");
    if (resetCmd) {
      consumption = 0;
      hourStartTime = millis();
      Serial.println("Consumption reset by dashboard!");
      Database.set<bool>(asyncClient, "/nodes/node2/commands/resetConsumption", false);
    }
  }
}