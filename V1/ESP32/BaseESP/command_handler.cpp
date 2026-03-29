#include "command_handler.h"
#include "config.h"

bool isValidCommand(const String &cmd) {
  if (cmd.length() < 2) return false;
  String c = cmd;
  c.toLowerCase();

  if (c == "launch" || c == "abort" || c == "go" ||
      c == "hold"   || c == "ignite" || c == "igniteoff") return true;

  if (c.length() >= 4 && c.charAt(1) == '_') {
    char id    = c.charAt(0);
    String st  = c.substring(2);
    return (id >= 'a' && id <= 'd') && (st == "on" || st == "off");
  }

  if (c.charAt(0) >= 'a' && c.charAt(0) <= 'd') {
    String numPart = c.substring(1);
    numPart.trim();
    if (numPart.length() > 0 && isDigit(numPart.charAt(0))) {
      int angle = numPart.toInt();
      return (angle >= 0 && angle <= 180);
    }
  }

  return false;
}

void checkSerialInput() {
  // Only accept new command if none is pending
  if (strlen(pendingCmd) != 0 || !Serial.available()) return;

  String input = Serial.readStringUntil('\n');
  input.trim();

  if (isValidCommand(input)) {
    input.toCharArray(pendingCmd, BUFFER_SIZE);
    Serial.printf("[CMD] queued \"%s\"\n", pendingCmd);
  } else if (input.length() > 0) {
    Serial.println("[CMD] unknown — valid commands:");
    Serial.println("  a_on/a_off   preset angles");
    Serial.println("  a90/a 90     direct angle (0-180)");
    Serial.println("  launch/abort sequences");
    Serial.println("  go/hold      sequence flow control");
    Serial.println("  ignite/igniteoff  fire pin");
  }
}