#include "Firebase_Arduino_WiFiNINA.h"
#include "secrets.h"
#include <WiFiNINA.h>

#include <AccelStepper.h>
#include <SPI.h>

#include <NewPing.h>

// Wifi Credentials
char ssid[] = SECRET_SSID;
char pass[] = SECRET_PASS;
char dataPath[] = "/position.json";
char fireBaseUrl[] = DATA_URL;

int wifiStatus = WL_IDLE_STATUS;
WiFiClient client;
int maxReconnect = 10;
int numReconnect = 0;

// Ultrasonic Sensor Pins & Object
const int triggerPin = 12;
const int echoPin = 11;
NewPing sonar(triggerPin, echoPin, 500);

// Hall Effect Sensor Pin
const int magnetSensorPin = 2;

// Variables for non-blocking delay in sensor readings.
unsigned long lastRead = 0;
unsigned long startMoveTime = 0;
const long interval = 600;
const long moveInterval = 400;

volatile int magnetCount = 0;
int currentPosition = 1;
int direction = 1;

// Stepper object
AccelStepper myStepper(AccelStepper::FULL4WIRE, 3, 5, 4, 6);

void setup() {
  // Connect to WiFi
  while(wifiStatus != WL_CONNECTED)
  {
    wifiStatus = WiFi.begin(ssid, pass);
    // Wait 5 seconds for connection.
    delay(5000);
  }

  // Configure stepper motor and reset positioning.
  myStepper.setMaxSpeed(1000);
  myStepper.setAcceleration(500);
  myStepper.setSpeed(200);
  moveToHome();

  // Connect to database
  connect();

  // Setup magnet sensor interrupt
  pinMode(magnetSensorPin, INPUT_PULLUP);
  attachInterrupt(digitalPinToInterrupt(magnetSensorPin), magnetDetected, RISING);

}


void loop() 
{
  String line = "";
  bool readingData = false;

  // Read data from Firebase
  while(client.available())
  {

    char c = client.read();
    if(c == '\n')
    { 
      if(line.startsWith("data:"))
      {
        readingData = true;
        line = line.substring(6);
      }
      else
      {
        line = "";
      }
      
      if(readingData)
      {
        int endOfData = line.lastIndexOf('}');
        int startOfData = line.lastIndexOf(':', endOfData - 1);
        
        String position = line.substring(startOfData + 1, endOfData);
        if(position != "null")
        {
          moveToPosition(position.toInt());
        }
        readingData = false;
        line = "";
      }
    }
    else
    {
      line += c;
    }
  }
}

void moveToHome()
{
  int dist = 0; 

  // Move stepper motor to the home position based on ultrasonic distance
  while(dist >= 7 || dist == 0)
  {

    dist = sonar.ping_cm();
    myStepper.runSpeed();
  }

  myStepper.stop();
}

void magnetDetected()
{
  unsigned long current = millis();
  if(current - lastRead >= interval && current - startMoveTime >= moveInterval)
  {
    magnetCount++;
     // Update current position with modulo to ensure it stays within the range of 1 to 12
    if(direction == 1)
    {
      currentPosition = (currentPosition + 1) % 12;
    }
    else
    {
      currentPosition = (currentPosition - 1 + 12) % 12;
    }
    lastRead = current;
  }
}

int calcMoves(int targetPosition)
{
  int clockwiseMoves = (targetPosition - currentPosition + 12) % 12;
  int counterClockwiseMoves = (currentPosition - targetPosition + 12) % 12;
  return (clockwiseMoves <= counterClockwiseMoves) ? clockwiseMoves : -counterClockwiseMoves;
}

void moveToPosition(int targetPosition)
{
  int stepsToMove = calcMoves(targetPosition);
  direction = (stepsToMove > 0) ? 1 : -1;
  stepsToMove = abs(stepsToMove);

  myStepper.setSpeed(200 * direction);
  magnetCount = 0;
  startMoveTime = millis();
  while(magnetCount < stepsToMove)
  {
    myStepper.runSpeed();
  }
  myStepper.stop();
}

void connect()
{
  // Connect to Firebase
  if(!client.connectSSL(fireBaseUrl, 443))
  {
    return;
  }
  // Send initial position to Firebase
  String jsonData = "{\"position\": 1}";
  
  client.println("PATCH /.json HTTP/1.1");
  client.println("Host: " + String(fireBaseUrl));
  client.println("Content-Type: application/json");
  client.print("Content-Length: ");
  client.println(jsonData.length());
  client.println("Connection: keep-alive");
  client.println();
  client.println(jsonData);

  // Start listening for data updates
  client.println("GET " + String(dataPath) + " HTTP/1.1");
  client.println("Host: " + String(fireBaseUrl));
  client.println("Accept: text/event-stream");
  client.println("Cache-Control: no-cache");
  client.println("Connection: keep-alive");
  client.println();
}
