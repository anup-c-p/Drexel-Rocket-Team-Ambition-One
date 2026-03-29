#pragma once
#include <ESP32Servo.h>

extern Servo servo_a, servo_b, servo_c, servo_d;

void initServos();
void dispatchServo(char servo_id, int preset_idx);
void handleCommand(String command);