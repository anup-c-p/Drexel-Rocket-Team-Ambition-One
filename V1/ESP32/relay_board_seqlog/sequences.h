#pragma once
#include "servo_sequencer.h"

// Launch with a hold before MPVs open — operator must confirm ignition is good
static const SequenceStep SEQ_LAUNCH[] = {
  servoStep('b', 1, 0), 
  waitInput(),
  servoStep('b', 0, 0),
  waitInput(),
  servoStep('d', 1, 500),  
  servoStep('c', 1, 200),
  actionStep(ignite,    500),  // pin HIGH, wait 10s
  actionStep(igniteOff, 0),
  servoStep('d', 0, 0),
  servoStep('c', 0, 10000),
  servoStep('d', 1, 0),
  waitInput(),
  servoStep('b', 1, 15000),
  servoStep('b', 0, 10000),
  servoStep('a', 1, 30000),
  servoStep('a', 0, 0),
  waitInput(),
  servoStep('a', 1, 15000),
  servoStep('b', 1, 0),
};

static const SequenceStep SEQ_ABORT[] = {
  actionStep(igniteOff,  0),  // kill igniter immediately
  servoStep('c', 0, 0),
  servoStep('d', 0, 0),
  servoStep('a', 0, 0),
  servoStep('b', 0, 10000),
  servoStep('d', 1, 0),
};

#define SEQ_LAUNCH_LEN (sizeof(SEQ_LAUNCH) / sizeof(SEQ_LAUNCH[0]))
#define SEQ_ABORT_LEN  (sizeof(SEQ_ABORT)  / sizeof(SEQ_ABORT[0]))