#include "sensors.h"
#include "config.h"
#include <Arduino.h>

// ── Oversampling config ──────────────────────────────────────────────────
static const uint8_t ADC_OVERSAMPLE = 16;

// ── channel index, v_min, v_max, max engineering value
struct PressureCh {
  uint8_t ch;
  float   vMin;
  float   vMax;
  float   maxPSIG;
};

static const PressureCh PRESSURE_CHANNELS[] = {
  { CH_PRESSURE_1, PRESSURE_V_MIN, PRESSURE_V_MAX, MAX_PRESSURE_PSIG },
  { CH_PRESSURE_2, PRESSURE_V_MIN, PRESSURE_V_MAX, MAX_PRESSURE_PSIG },
  { CH_PRESSURE_3, PRESSURE_V_MIN, PRESSURE_V_MAX, MAX_PRESSURE_PSIG },
};

// ── 16-sample mean average (returns volts) ───────────────────────────────
static float readChannel_Avg(uint8_t channel) {
  float sum = 0.0f;
  for (uint8_t i = 0; i < ADC_OVERSAMPLE; i++) {
    sum += ads.computeVolts(ads.readADC_SingleEnded(channel));
  }
  return sum / ADC_OVERSAMPLE;
}

void readSensors(SensorData& d) {
  d.timestamp_ms = millis();

  // ── Pressure channels ──────────────────────────────────────────────────
  for (int i = 0; i < 3; i++) {
    const PressureCh& p = PRESSURE_CHANNELS[i];
    float v = readChannel_Avg(p.ch);
    d.vPressure[i]     = v;
    d.pressure_psig[i] = constrain(
      (v - p.vMin) / (p.vMax - p.vMin) * p.maxPSIG,
      0.0f, p.maxPSIG);
  }

  // ── Force channel ──────────────────────────────────────────────────────
  float vF   = readChannel_Avg(CH_FORCE);
  d.vForce   = vF;
  d.force_kg = constrain(
    constrain(vF, 0.0f, 6.144f)
      / (INA125_GAIN * LOAD_CELL_SENS * BRIDGE_EXCITATION)
      * MAX_FORCE_KG,
    0.0f, MAX_FORCE_KG);
}

void checkThresholds(const SensorData& d) {
  digitalWrite(PRESSURE_ALERT_PIN, d.vPressure[0] < PRESSURE_THRESHOLD_V);
}