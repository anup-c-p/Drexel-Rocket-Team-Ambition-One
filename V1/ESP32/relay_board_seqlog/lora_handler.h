#pragma once
#include "LoRaWan_APP.h"

extern char latestSensorRow[];
extern char txpacket[];
extern char rxpacket[];

void initLoRa();
void OnTxDone();
void OnTxTimeout();
void OnRxDone(uint8_t *payload, uint16_t size, int16_t rssi, int8_t snr);