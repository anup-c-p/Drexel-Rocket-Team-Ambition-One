#include "abort_interrupt.h"
#include "config.h"

// volatile tells the compiler this can change outside normal program flow
static volatile bool _abortFlag = false;

// IRAM_ATTR forces this function into RAM — required for ESP32 ISRs
void IRAM_ATTR onAbortTriggered() {
  _abortFlag = true;
}

void initAbortInterrupt() {
  pinMode(ABORT_PIN, INPUT_PULLUP);
  // FALLING = pin goes LOW when button is pressed (pulled up to HIGH at rest)
  attachInterrupt(digitalPinToInterrupt(ABORT_PIN), onAbortTriggered, FALLING);
  Serial.println("[ABORT] interrupt armed");
}

bool abortFlagRaised() { return _abortFlag; }
void clearAbortFlag()  { _abortFlag = false; }