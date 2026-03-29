#pragma once
#include "sensor_data.h"

void readSensors(SensorData& d);

void checkThresholds(const SensorData& d);