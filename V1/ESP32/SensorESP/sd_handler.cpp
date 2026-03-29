#include "sd_handler.h"
#include "config.h"
#include <SD.h>

bool sdReady = false;

void initSD(){
  if (!SD.begin(SD_CS)) {
    Serial.println("WARN: SD card not found — logging disabled.");
  } else {
    sdReady = true;
    Serial.println("SD card ready.");

    // Write CSV header if file doesn't already exist
    if (!SD.exists(LOG_FILE)) {
      File f = SD.open(LOG_FILE, FILE_WRITE);
      if (f) {
        f.println("millis,Pressure_V,Pressure_PSIG,Force_V,Force_kg");
        f.close();
      }
    }
  }
}

void writeSD(const SensorData& d) {
  if (!sdReady) return;
  char row[80];
  formatRow(d, row, sizeof(row));
  File f = SD.open(LOG_FILE, FILE_APPEND);
  if (f) { f.println(row); f.close(); }
  else Serial.println("WARN: Could not open log file.");
}