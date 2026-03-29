#include "sensor_data.h"
#include <stdio.h>

void formatRow(const SensorData& d, char* buf, size_t bufLen) {
  snprintf(buf, bufLen,
    "%lu,%.4f,%.4f,%.4f,%.4f",
    d.timestamp_ms,
    d.vPressure[0],
    d.vPressure[1],
    d.vPressure[2],
    d.vForce);
}