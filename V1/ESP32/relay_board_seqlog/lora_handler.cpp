#include "lora_handler.h"
#include "servo_control.h"
#include "servo_sequencer.h"
#include "config.h"

char latestSensorRow[BUFFER_SIZE] = "0,0.0000,0.0000,0.0000,0.0000";
char txpacket[BUFFER_SIZE];
char rxpacket[BUFFER_SIZE];

static RadioEvents_t RadioEvents;

void initLoRa() {
  Mcu.begin(HELTEC_BOARD, SLOW_CLK_TPYE);
  RadioEvents.TxDone    = OnTxDone;
  RadioEvents.TxTimeout = OnTxTimeout;
  RadioEvents.RxDone    = OnRxDone;
  Radio.Init(&RadioEvents);
  Radio.SetChannel(RF_FREQUENCY);
  Radio.SetTxConfig(MODEM_LORA, TX_OUTPUT_POWER, 0, LORA_BANDWIDTH,
                    LORA_SPREADING_FACTOR, LORA_CODINGRATE,
                    LORA_PREAMBLE_LENGTH, LORA_FIX_LENGTH_PAYLOAD_ON,
                    true, 0, 0, LORA_IQ_INVERSION_ON, 3000);
  Radio.SetRxConfig(MODEM_LORA, LORA_BANDWIDTH, LORA_SPREADING_FACTOR,
                    LORA_CODINGRATE, 0, LORA_PREAMBLE_LENGTH,
                    LORA_SYMBOL_TIMEOUT, LORA_FIX_LENGTH_PAYLOAD_ON,
                    0, true, 0, 0, LORA_IQ_INVERSION_ON, true);
  Radio.Rx(0);
  Serial.println("[LoRa] ready");
}

// ── Helpers ───────────────────────────────────────────────────

// Appends sequencer status to every response so base station always knows state.
// Format: "BUSY" | "WAITING" | "IDLE"
static const char* sequencerStatus() {
  if (sequencerWaiting()) return "WAITING";
  if (sequencerBusy())    return "BUSY";
  return "IDLE";
}

static void sendResponse() {
  delay(10);  // guard time before TX
  Serial.printf("[LoRa TX] \"%s\"\n", txpacket);
  Radio.Send((uint8_t*)txpacket, strlen(txpacket));
}

// ── Callbacks ─────────────────────────────────────────────────
void OnRxDone(uint8_t *payload, uint16_t size, int16_t rssi, int8_t snr) {
  size = min((uint16_t)(BUFFER_SIZE - 1), size);
  memcpy(rxpacket, payload, size);
  rxpacket[size] = '\0';
  Radio.Sleep();

  Serial.printf("[LoRa RX] \"%s\"  rssi=%d\n", rxpacket, rssi);

  if (strncmp(rxpacket, "POLL", 4) != 0) {
    Serial.println("[RX] ignored — not a POLL");
    Radio.Rx(0);
    return;
  }

  if (rxpacket[4] == ':') {
    // POLL:<cmd> — execute command, respond with sensor row + ACK + sequencer state
    // Examples: POLL:a_on  POLL:a90  POLL:launch  POLL:go  POLL:ignite
    String cmd = String(rxpacket).substring(5);
    cmd.trim();
    handleCommand(cmd);
    snprintf(txpacket, BUFFER_SIZE, "%s|ACK:%s|SEQ:%s",
             latestSensorRow, cmd.c_str(), sequencerStatus());
  } else {
    // POLL — plain data request, still include sequencer state
    snprintf(txpacket, BUFFER_SIZE, "%s|SEQ:%s",
             latestSensorRow, sequencerStatus());
    if (strlen(seqLogBuf) > 0) {
      strncat(txpacket, "|LOG:", BUFFER_SIZE - strlen(txpacket) - 1);
      strncat(txpacket, seqLogBuf, BUFFER_SIZE - strlen(txpacket) - 1);
      clearSeqLog();
    }
  }

  sendResponse();
}

void OnTxDone(void) {
  Serial.println("[LoRa] TX done, back to RX");
  Radio.Rx(0);
}

void OnTxTimeout(void) {
  Serial.println("[LoRa] TX timeout, returning to RX");
  Radio.Standby();
  delay(10);
  Radio.Rx(0);
}