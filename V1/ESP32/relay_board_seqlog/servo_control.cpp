#include "servo_control.h"
#include "config.h"
#include "sequences.h"
#include "servo_sequencer.h"

// ── Servo instances ───────────────────────────────────────────
Servo servo_a, servo_b, servo_c, servo_d;
static Servo* servoMap[] = { &servo_a, &servo_b, &servo_c, &servo_d };
static const int servoPins[] = { SERVO_PIN_A, SERVO_PIN_B, SERVO_PIN_C, SERVO_PIN_D };

void initServos() {
  for (int i = 0; i < 4; i++) {
    servoMap[i]->setPeriodHertz(50);
    servoMap[i]->attach(servoPins[i], SERVO_MIN_PULSE, SERVO_MAX_PULSE);
  }
  pinMode(FIRE_PIN, OUTPUT);
  digitalWrite(FIRE_PIN, LOW);
}
void dispatchServo(char servo_id, int preset_idx) {
  int row = servo_id - 'a';
  if (row < 0 || row > 3) {
    Serial.printf("[CMD] unknown servo: '%c'\n", servo_id); return;
  }
  if (preset_idx != 0 && preset_idx != 1) {
    Serial.printf("[CMD] invalid preset: %d\n", preset_idx); return;
  }
  int angle = SERVO_PRESETS[row][preset_idx];
  servoMap[row]->write(angle);
  Serial.printf("[CMD] servo %c %s -> %d°\n", servo_id, preset_idx ? "on" : "off", angle);
}

void handleCommand(String command) {
  command.trim();
  command.toLowerCase();

  if (command == "launch")    { runSequence(SEQ_LAUNCH, SEQ_LAUNCH_LEN); return; }
  if (command == "abort")     { abortSequence(); runSequence(SEQ_ABORT, SEQ_ABORT_LEN); return; }
  if (command == "go")        { confirmSequence(); return; }
  if (command == "hold")      { abortSequence(); return; }
  if (command == "ignite")    { ignite();    return; }
  if (command == "igniteoff") { igniteOff(); return; }

  // "a_on" / "a_off"
  if (command.length() >= 4 && command.charAt(1) == '_') {
    char servo_id = command.charAt(0);
    String state  = command.substring(2);
    if (state == "on")  { dispatchServo(servo_id, 1); return; }
    if (state == "off") { dispatchServo(servo_id, 0); return; }
  }

  // "a90" or "a 90" — direct angle write
  if (command.length() >= 2 && command.charAt(0) >= 'a' && command.charAt(0) <= 'd') {
    char servo_id  = command.charAt(0);
    String numPart = command.substring(1);
    numPart.trim();   // handles "a 90" with a space

    if (numPart.length() > 0 && isDigit(numPart.charAt(0))) {
      int angle = numPart.toInt();
      if (angle < 0 || angle > 180) {
        Serial.printf("[CMD] angle %d out of range (0-180)\n", angle); return;
      }
      int row = servo_id - 'a';
      servoMap[row]->write(angle);
      Serial.printf("[CMD] servo %c -> %d° (direct)\n", servo_id, angle);
      return;
    }
  }

  Serial.printf("[CMD] unknown command: \"%s\"\n", command.c_str());
}