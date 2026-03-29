#pragma once
#include <stddef.h>  // ← gives you size_t
#include <stdint.h>  // ← gives you uint32_t

struct SensorData {
  uint32_t timestamp_ms;
  float    vPressure[3];
  float    pressure_psig[3];
  float    vForce;
  float    force_kg;
};

// fills a pre-allocated char buffer with the CSV row
void formatRow(const SensorData& d, char* buf, size_t bufLen);