#pragma once
#include <Arduino.h>

void initAbortInterrupt();
bool abortFlagRaised();
void clearAbortFlag();