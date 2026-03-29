#pragma once
#include <Arduino.h>

enum StepType {
  STEP_SERVO,       // fire a servo, then wait delay_ms
  STEP_WAIT_INPUT,  // block until confirmSequence() is called
  STEP_DELAY,       // just wait delay_ms, no servo action
  STEP_ACTION,      // call a function, then wait delay_ms
};

struct SequenceStep {
  StepType type;
  char     servo_id;   // used by STEP_SERVO only
  int      preset_idx; // used by STEP_SERVO only
  uint32_t delay_ms;   // used by STEP_SERVO and STEP_DELAY
  void      (*action)();   // used by STEP_ACTION only, nullptr otherwise
};

// Convenience constructors — keeps sequences.h readable
inline SequenceStep servoStep(char id, int preset, uint32_t delay) {
  return { STEP_SERVO, id, preset, delay, nullptr };
}
inline SequenceStep waitInput() {
  return { STEP_WAIT_INPUT, 0, 0, 0, nullptr };
}
inline SequenceStep delayStep(uint32_t ms) {
  return { STEP_DELAY, 0, 0, ms, nullptr };
}
inline SequenceStep actionStep(void (*fn)(), uint32_t delay) {
  return { STEP_ACTION, 0, 0, delay, fn };
}

extern char seqLogBuf[];
void seqLog(const char* fmt, ...);
void clearSeqLog();

void runSequence(const SequenceStep* steps, int count);
void confirmSequence();   // call this to unblock a WAIT_INPUT step
void abortSequence();     // cancel mid-sequence if needed
void tickSequencer();
void ignite();
void igniteOff();

bool sequencerBusy();
bool sequencerWaiting();  // true if paused on a WAIT_INPUT