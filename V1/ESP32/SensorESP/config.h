#pragma once
#include <Adafruit_ADS1X15.h>

#define SD_CS       5
#define LOG_FILE    "/datalog.csv"
#define SERIAL2_BAUD  115200
#define ADS_GAIN  GAIN_TWOTHIRDS  // ±6.144V FSR
#define ADS_RATE  RATE_ADS1115_128SPS

// ── ADS1115 Channel Map ───────────────────────────────────────────────────
#define CH_FORCE        0
#define CH_PRESSURE_1   1
#define CH_PRESSURE_2   2
#define CH_PRESSURE_3   3

extern Adafruit_ADS1115 ads;

#define PRESSURE_ALERT_PIN    33
#define PRESSURE_THRESHOLD_V    4.8f

// ─── Pressure Sensor (A0) ─────────────────────────────────────────────────
const float MAX_PRESSURE_PSIG = 1000.0;
const float PRESSURE_V_MIN    = 0.0f;
const float PRESSURE_V_MAX    = 5.0f;

// ─── Force Sensor / INA125P (A1) ──────────────────────────────────────────
const float INA125_RG         = 330.0f;
const float INA125_GAIN       = 4.0f + (60000.0f / INA125_RG);
const float BRIDGE_EXCITATION = 5.0f;
const float LOAD_CELL_SENS    = 0.003f;
const float MAX_FORCE_KG      = 250.0f;