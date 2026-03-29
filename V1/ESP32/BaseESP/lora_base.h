#pragma once
#include "LoRaWan_APP.h"
#include "Arduino.h"

typedef enum { STATE_RX, STATE_TX } States_t;

extern States_t   state;
extern char       txpacket[];
extern char       rxpacket[];
extern char       pendingCmd[];
extern bool       waitingForRx;
extern uint8_t    retryCount;
extern unsigned long lastPollAt;

void initLoRa();
void sendPoll();
void checkRetryTimeout();

void OnTxDone(void);
void OnTxTimeout(void);
void OnRxDone(uint8_t *payload, uint16_t size, int16_t rssi, int8_t snr);