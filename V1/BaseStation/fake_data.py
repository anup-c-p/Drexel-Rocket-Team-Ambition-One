import queue
import random
import time

_fake_t = 0

def fake_lines():
    """Yield one batch of realistic fake serial lines per call."""
    global _fake_t
    lines = []
    for _ in range(random.randint(2, 4)):
        lines.append('[Poll] "POLL"\n')
    if random.random() < 0.3:
        lines.append('[LoRa] poll sent, waiting for response\n')
    if random.random() < 0.2:
        lines.append('[SEQ] IDLE\n')
    if random.random() < 0.5:
        _fake_t += random.randint(800, 1200)
        vP0  = round(random.uniform(0.004, 0.007), 4)
        vP1  = round(random.uniform(0.40,  0.50),  4)
        vP2  = round(random.uniform(0.004, 0.007), 4)
        vF   = round(random.uniform(0.10,  0.15),  4)
        rssi = random.randint(-20, -5)
        sa, sb, sc, sd = (random.randint(0, 1) for _ in range(4))
        lines.append(
            f'[Sensor] t={_fake_t}ms '
            f'vP0={vP0:.4f}V vP1={vP1:.4f}V vP2={vP2:.4f}V '
            f'vF={vF:.4f}V rssi={rssi}\n'
        )
        lines.append(f' a={sa} b={sb} c={sc} d={sd}\n')
    return lines


def fake_loop(rx_queue, is_running):
    """Thread target: feeds fake lines into rx_queue while is_running() is True."""
    global _fake_t
    _fake_t = 0   # reset counter on each new session
    start = time.time()
    while is_running():
        # ── Abort test: uncomment the block below to inject 5V on vP0 ─────────
        #for line in _abort_test_lines(time.time() - start):
        #     try:
        #         rx_queue.put_nowait(line)
        #     except queue.Full:
        #         pass
        # ──────────────────────────────────────────────────────────────────────
        for line in fake_lines():
            try:
                rx_queue.put_nowait(line)
            except queue.Full:
                pass  # drop rather than block if the main thread is stalled
        time.sleep(random.uniform(0.3, 0.6))


def _abort_test_lines(elapsed):
    """Inject a sensor line with vP0=5.0V for the first 10 seconds of the session."""
    global _fake_t
    if elapsed > 10:
        return []
    _fake_t += random.randint(800, 1200)
    vP1  = round(random.uniform(0.40, 0.50), 4)
    vP2  = round(random.uniform(0.004, 0.007), 4)
    vF   = round(random.uniform(0.10, 0.15), 4)
    rssi = random.randint(-20, -5)

    return [
        f'[Sensor] t={_fake_t}ms '
        f'vP0=5.0000V vP1={vP1:.4f}V vP2={vP2:.4f}V '
        f'vF={vF:.4f}V rssi={rssi}\n',
        f' a=0 b=0 c=0 d=0\n',
    ]
