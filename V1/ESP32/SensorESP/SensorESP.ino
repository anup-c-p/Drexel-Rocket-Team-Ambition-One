#include <Wire.h>
#include <SPI.h>
#include "config.h"
#include "sd_handler.h"
#include "sensors.h"

Adafruit_ADS1115 ads;

void setup() {
  Serial.begin(115200);
  Serial2.begin(SERIAL2_BAUD);   // TX=GPIO17, RX=GPIO16 (to Heltec)
  Wire.begin(21, 22, 100000); // force 100kHz instead of 400kHzx`

  pinMode(PRESSURE_ALERT_PIN, OUTPUT);
  digitalWrite(PRESSURE_ALERT_PIN, HIGH);


  // ── ADS1115 ──────────────────────────────────────────────────────────────
  if (!ads.begin()) {
    Serial.println("ERROR: ADS1115 not found. Check wiring.");
    while (1);
  }
  ads.setGain(ADS_GAIN);
  ads.setDataRate(ADS_RATE);

  initSD();

  Serial.println("Pressure_V\tPressure_PSIG\tForce_V\tForce_kg");
}

void loop() {
  SensorData d;
  readSensors(d);
  checkThresholds(d);

  char row[120];
  formatRow(d, row, sizeof(row));

  Serial.println(row);
  Serial2.println(row);
  writeSD(d);

  delay(50);
}