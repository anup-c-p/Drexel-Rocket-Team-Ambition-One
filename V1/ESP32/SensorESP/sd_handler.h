#pragma once
#include "sensor_data.h"

extern bool sdReady;

void initSD();
void writeSD(const SensorData& d);