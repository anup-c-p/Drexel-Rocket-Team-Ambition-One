#pragma once

// Serial1 (sensor ESP32)
#define SENSOR_SERIAL_BAUD 115200
#define SENSOR_RX_PIN      47
#define SENSOR_TX_PIN      48
#define BUFFER_SIZE        128

// LoRa
#define RF_FREQUENCY           915000000
#define TX_OUTPUT_POWER        14
#define LORA_BANDWIDTH         0
#define LORA_SPREADING_FACTOR  7
#define LORA_CODINGRATE        1
#define LORA_PREAMBLE_LENGTH   8
#define LORA_SYMBOL_TIMEOUT    0
#define LORA_FIX_LENGTH_PAYLOAD_ON false
#define LORA_IQ_INVERSION_ON       false

//Igniter pin
#define FIRE_PIN 7

//Abort interrupt
#define ABORT_PIN 6

// Servo pins
#define SERVO_PIN_A 4
#define SERVO_PIN_B 5
#define SERVO_PIN_C 3
#define SERVO_PIN_D 2
#define SERVO_MIN_PULSE 500
#define SERVO_MAX_PULSE 2500

// Servo presets [servo_index][0=closed, 1=open]
const int SERVO_PRESETS[][2] = {
  { 179, 116 }, // GSE_nitro
  { 179, 116 }, // GSE_n2o
  { 105, 39  }, // MPV_fuel
  { 179, 115 }, // MPV_n2o
};