#include "config.h"
#include "lora_base.h"
#include "command_handler.h"

void setup() {
  Serial.begin(115200);
  initLoRa();
  Serial.println("Base station ready.");
}

void loop() {
  Radio.IrqProcess();
  checkSerialInput();
  checkRetryTimeout();

  switch (state) {
    case STATE_RX:
      if (!waitingForRx && (millis() - lastPollAt >= POLL_INTERVAL_MS)) {
        Radio.Standby();
        delay(10);
        state = STATE_TX;
      }
      break;

    case STATE_TX:
      sendPoll();
      break;
  }
}