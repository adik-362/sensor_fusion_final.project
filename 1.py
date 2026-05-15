#include <Wire.h>
#include "Waveshare_LCD1602_RGB.h"

Waveshare_LCD1602_RGB lcd(16, 2);

// Sensors
#define TRIG1 12
#define ECHO1 11
#define TRIG2 7
#define ECHO2 6

// LEDs
#define RED_LED 3
#define GREEN_LED 2

// Logic
#define DETECT_THRESHOLD 15   // чуть увеличили для стабильности
#define TIME_LIMIT 2000       // 🔥 2.0 секунды (как ты попросил)

bool carDetected = false;
unsigned long timeStart = 0;

// ===============================
// 📌 FILTERED DISTANCE (VERY IMPORTANT)
// ===============================
float readDistanceOnce(int trigPin, int echoPin) {
  digitalWrite(trigPin, LOW);
  delayMicroseconds(2);

  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPin, LOW);

  long duration = pulseIn(echoPin, HIGH, 30000);

  if (duration == 0) return 999; // no echo

  return (duration * 0.0343) / 2.0;
}

// average filter (removes noise)
float getDistance(int trigPin, int echoPin) {
  float sum = 0;
  int valid = 0;

  for (int i = 0; i < 3; i++) {
    float d = readDistanceOnce(trigPin, echoPin);

    if (d > 2 && d < 200) { // ignore noise
      sum += d;
      valid++;
    }
    delay(10);
  }

  if (valid == 0) return 999;
  return sum / valid;
}

// ===============================
void setup() {
  Wire.begin();

  lcd.init();
  lcd.clear();
  lcd.setRGB(0, 255, 0);

  pinMode(TRIG1, OUTPUT);
  pinMode(ECHO1, INPUT);
  pinMode(TRIG2, OUTPUT);
  pinMode(ECHO2, INPUT);

  pinMode(RED_LED, OUTPUT);
  pinMode(GREEN_LED, OUTPUT);

  digitalWrite(RED_LED, LOW);
  digitalWrite(GREEN_LED, LOW);

  Serial.begin(9600);

  lcd.setCursor(0, 0);
  lcd.send_string("Speed Meter");
  lcd.setCursor(0, 1);
  lcd.send_string("Waiting...");
}

// ===============================
void loop() {

  float d1 = getDistance(TRIG1, ECHO1);
  float d2 = getDistance(TRIG2, ECHO2);

  // DEBUG (очень важно)
  Serial.print("D1: "); Serial.print(d1);
  Serial.print(" | D2: "); Serial.println(d2);

  // SENSOR 1
  if (!carDetected && d1 < DETECT_THRESHOLD) {
    timeStart = millis();
    carDetected = true;

    lcd.setCursor(0, 1);
    lcd.send_string("Car detected... ");
  }

  // SENSOR 2
  if (carDetected && d2 < DETECT_THRESHOLD) {

    unsigned long timeEnd = millis();
    unsigned long deltaTime = timeEnd - timeStart;

    float timeSec = deltaTime / 1000.0;

    lcd.setCursor(0, 0);
    lcd.send_string("Time:           ");
    lcd.setCursor(6, 0);
    lcd.send_string(String(timeSec, 2).c_str());

    lcd.setCursor(0, 1);
    lcd.send_string("Status:         ");

    // ===============================
    // 🔥 MAIN LOGIC (3 seconds rule)
    // ===============================
    if (deltaTime <= TIME_LIMIT) {
      // OVER (too fast → red)
      lcd.setRGB(255, 0, 0);
      lcd.setCursor(8, 1);
      lcd.send_string("OVER");

      digitalWrite(RED_LED, HIGH);
      digitalWrite(GREEN_LED, LOW);

      Serial.println(">>> OVER SPEED <<<");
    } 
    else {
      // NORMAL (good → green)
      lcd.setRGB(0, 255, 0);
      lcd.setCursor(8, 1);
      lcd.send_string("NORMAL");

      digitalWrite(RED_LED, LOW);
      digitalWrite(GREEN_LED, HIGH);

      Serial.println(">>> NORMAL <<<");
    }

    delay(3000);

    carDetected = false;

    digitalWrite(RED_LED, LOW);
    digitalWrite(GREEN_LED, LOW);

    lcd.setCursor(0, 0);
    lcd.send_string("Speed Meter     ");
    lcd.setCursor(0, 1);
    lcd.send_string("Waiting...      ");
  }

  // TIMEOUT RESET
  if (carDetected && millis() - timeStart > 7000) {
    carDetected = false;

    lcd.setCursor(0, 1);
    lcd.send_string("Timeout!        ");

    digitalWrite(RED_LED, LOW);
    digitalWrite(GREEN_LED, LOW);

    delay(1000);

    lcd.setCursor(0, 0);
    lcd.send_string("Speed Meter     ");
    lcd.setCursor(0, 1);
    lcd.send_string("Waiting...      ");
  }

  delay(30);
}