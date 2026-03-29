#include "servo_sequencer.h"
#include "servo_control.h"
#include "config.h"
#include <stdarg.h>

static const SequenceStep* _steps     = nullptr;
static int                 _count     = 0;
static int                 _current   = -1;
static uint32_t            _stepStart = 0;
static bool                _waiting   = false;
static bool                _holdInput = false;  // parked on WAIT_INPUT

bool sequencerBusy()    { return _current >= 0; }
bool sequencerWaiting() { return _holdInput; }

char seqLogBuf[BUFFER_SIZE] = "";

void seqLog(const char* fmt, ...) {
  char tmp[BUFFER_SIZE];
  va_list args;
  va_start(args, fmt);
  vsnprintf(tmp, sizeof(tmp), fmt, args);
  va_end(args);

  Serial.print(tmp);                          // still prints to serial
  strncat(seqLogBuf, tmp, BUFFER_SIZE - strlen(seqLogBuf) - 1);  // append to buffer
}

void clearSeqLog() { seqLogBuf[0] = '\0'; }

void runSequence(const SequenceStep* steps, int count) {
  if (_current >= 0) {
    seqLog("[SEQ] already running, ignoring\n");
    return;
  }
  _steps     = steps;
  _count     = count;
  _current   = 0;
  _waiting   = false;
  _holdInput = false;
  seqLog("[SEQ] starting (%d steps)\n", count);
}

void confirmSequence() {
  if (_holdInput) {
    seqLog("[SEQ] input confirmed, resuming\n");
    _holdInput = false;
    _current++;
    _waiting = false;
  }
}

void abortSequence() {
  igniteOff(); 
  _current   = -1;
  _holdInput = false;
  _waiting   = false;
  seqLog("[SEQ] aborted\n");
}

void tickSequencer() {
  if (_current < 0 || _current >= _count) return;
  if (_holdInput) return;   // parked — nothing to do until confirm

  const SequenceStep& s = _steps[_current];

  if (!_waiting) {
    switch (s.type) {

      case STEP_SERVO:
        seqLog("[SEQ] step %d — servo %c preset %d\n",
                      _current, s.servo_id, s.preset_idx);
        dispatchServo(s.servo_id, s.preset_idx);
        _stepStart = millis();
        _waiting   = true;
        break;

      case STEP_DELAY:
        seqLog("[SEQ] step %d — delay %lums\n", _current, s.delay_ms);
        _stepStart = millis();
        _waiting   = true;
        break;

      case STEP_ACTION:
        if (s.action) s.action();   // call the entry function (e.g. ignite)
        _stepStart = millis();
        _waiting   = true;
        break;

      case STEP_WAIT_INPUT:
        seqLog("[SEQ] waiting for confirmation...\n");
        _holdInput = true;
        return;
    }
  }

  // Advance once delay has elapsed (STEP_SERVO and STEP_DELAY only)
  if (_waiting && millis() - _stepStart >= s.delay_ms) {
    if (s.type == STEP_ACTION && s.action == ignite) {
      igniteOff();
    }
    _current++;
    _waiting = false;
    if (_current >= _count) {
      seqLog("[SEQ] complete\n");
      _current = -1;
    }
  }
}

void ignite() {
  digitalWrite(FIRE_PIN, HIGH);
  seqLog("[IGN] firing\n");
}

void igniteOff() {
  digitalWrite(FIRE_PIN, LOW);
  seqLog("[IGN] done\n");
}