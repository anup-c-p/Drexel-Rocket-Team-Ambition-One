#pragma once
#include <Arduino.h>

extern char pendingCmd[];

bool isValidCommand(const String &cmd);
void checkSerialInput();