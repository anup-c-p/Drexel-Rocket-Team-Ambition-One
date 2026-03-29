#pragma once

// LoRa (must match relay exactly)
#define RF_FREQUENCY           915000000
#define TX_OUTPUT_POWER        14
#define LORA_BANDWIDTH         0
#define LORA_SPREADING_FACTOR  7
#define LORA_CODINGRATE        1
#define LORA_PREAMBLE_LENGTH   8
#define LORA_SYMBOL_TIMEOUT    0
#define LORA_FIX_LENGTH_PAYLOAD_ON false
#define LORA_IQ_INVERSION_ON       false
#define BUFFER_SIZE            128

// Poll / retry timing
#define POLL_INTERVAL_MS  500
#define ACK_TIMEOUT_MS    1000
#define MAX_RETRIES       5