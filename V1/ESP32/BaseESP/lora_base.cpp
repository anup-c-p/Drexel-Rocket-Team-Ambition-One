#include "lora_base.h"
#include "config.h"

char          txpacket[BUFFER_SIZE];
char          rxpacket[BUFFER_SIZE];
char          pendingCmd[BUFFER_SIZE] = "";
States_t      state        = STATE_RX;
bool          waitingForRx = false;
uint8_t       retryCount   = 0;
unsigned long lastPollAt   = 0;
int16_t       Rssi         = 0;

static RadioEvents_t RadioEvents;

// ── Init ──────────────────────────────────────────────────────
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
}

// ── Poll ──────────────────────────────────────────────────────
void sendPoll() {
  if (strlen(pendingCmd) > 0)
    snprintf(txpacket, BUFFER_SIZE, "POLL:%s", pendingCmd);
  else
    strncpy(txpacket, "POLL", BUFFER_SIZE);

  Serial.printf("[Poll] \"%s\"\n", txpacket);
  Radio.Send((uint8_t*)txpacket, strlen(txpacket));
  lastPollAt   = millis();
  waitingForRx = false;
}

// ── Retry logic ───────────────────────────────────────────────
void checkRetryTimeout() {
  if (!waitingForRx || (millis() - lastPollAt < ACK_TIMEOUT_MS)) return;

  waitingForRx = false;
  if (retryCount < MAX_RETRIES) {
    retryCount++;
    Serial.printf("[RETRY] no response, attempt %d/%d\n", retryCount, MAX_RETRIES);
    Radio.Standby();
    delay(10);
    state = STATE_TX;
  } else {
    Serial.println("[FAIL] relay not responding, dropping command");
    retryCount    = 0;
    pendingCmd[0] = '\0';
    state         = STATE_RX;
  }
}

// ── Callbacks ─────────────────────────────────────────────────
void OnTxDone(void) {
  Radio.Rx(0);
  waitingForRx = true;
  state        = STATE_RX;
  Serial.println("[LoRa] poll sent, waiting for response");
}

void OnTxTimeout(void) {
  Serial.println("[LoRa] TX timeout, retrying");
  Radio.Standby();
  delay(10);
  state = STATE_TX;
}

void OnRxDone(uint8_t *payload, uint16_t size, int16_t rssi, int8_t snr) {
  Rssi = rssi;
  size = min((uint16_t)(BUFFER_SIZE - 1), size);
  memcpy(rxpacket, payload, size);
  rxpacket[size] = '\0';
  Radio.Sleep();

  waitingForRx = false;
  retryCount   = 0;

  // Split response on '|' into up to 3 parts
  String response = String(rxpacket);
  String parts[3];
  int partCount = 0, start = 0;
  for (int i = 0; i <= (int)response.length() && partCount < 3; i++) {
    if (i == (int)response.length() || response.charAt(i) == '|') {
      parts[partCount++] = response.substring(start, i);
      start = i + 1;
    }
  }

  // Part 0 — sensor data
  unsigned long ts;
  float vP0, vP1, vP2, vForce;
  if (sscanf(parts[0].c_str(), "%lu,%f,%f,%f,%f",
            &ts, &vP0, &vP1, &vP2, &vForce) == 5) {
    Serial.printf("[Sensor] t=%lums  vP0=%.4fV  vP1=%.4fV  vP2=%.4fV  vF=%.4fV  rssi=%d\n",
                  ts, vP0, vP1, vP2, vForce, Rssi);
  } else {
    Serial.printf("[Relay] \"%s\"  rssi=%d\n", rxpacket, Rssi);
  }

  // Parts 1..2 — ACK and SEQ
  for (int i = 1; i < partCount; i++) {
    if (parts[i].startsWith("ACK:")) {
      String expected = "ACK:" + String(pendingCmd);
      if (parts[i] == expected) {
        Serial.printf("[ACK] confirmed: \"%s\"\n", pendingCmd);
        pendingCmd[0] = '\0';
      } else {
        Serial.printf("[WARN] unexpected ACK: \"%s\"\n", parts[i].c_str());
      }
    } else if (parts[i].startsWith("SEQ:")) {
      String seqState = parts[i].substring(4);
      Serial.printf("[SEQ] %s\n", seqState.c_str());
      if (seqState == "WAITING")
        Serial.println("[SEQ] >>> send \"go\" to confirm or \"hold\" to abort");
    }
    } else if (parts[i].startsWith("LOG:")) {
      Serial.printf("[SEQ] %s\n", parts[i].substring(4).c_str());
    }
  }

  state = STATE_RX;
}