#include "config.h"
#include "servo_control.h"
#include "lora_handler.h"
#include "servo_sequencer.h"
#include "sequences.h"
#include "abort_interrupt.h"

void setup() {
  Serial.begin(115200);
  Serial1.begin(SENSOR_SERIAL_BAUD, SERIAL_8N1, SENSOR_RX_PIN, SENSOR_TX_PIN);
  initServos();
  initLoRa();
  initAbortInterrupt();
  Serial.println("Relay ready — listening for polls.");
}

void loop() {

  if (abortFlagRaised()) {
    clearAbortFlag();
    abortSequence();
    runSequence(SEQ_ABORT, SEQ_ABORT_LEN);
    Serial.println("[ABORT] hardware interrupt triggered");
  }

  Radio.IrqProcess();
  tickSequencer(); 
  
  if (Serial1.available()) {
    String line = Serial1.readStringUntil('\n');
    line.trim();
    if (line.length() > 0) line.toCharArray(latestSensorRow, BUFFER_SIZE);
  }

  if (Serial.available()) handleCommand(Serial.readStringUntil('\n'));
}