from rtlsdr import RtlSdr
import numpy as np
import time

PMR_CHANNELS = {
    1: 446.00625e6,
    2: 446.01875e6,
    3: 446.03125e6,
    4: 446.04375e6,
    5: 446.05625e6,
    6: 446.06875e6,
    7: 446.08125e6,
    8: 446.09375e6,
    9: 446.10625e6,
    10: 446.11875e6,
    11: 446.13125e6,
    12: 446.14375e6,
    13: 446.15625e6,
    14: 446.16875e6,
    15: 446.18125e6,
    16: 446.19375e6
}

SAMPLE_RATE = 2.4e6
GAIN = 'auto'
SAMPLES = 256 * 1024
THRESHOLD_DB = -35   # à ajuster selon ton environnement RF

sdr = RtlSdr()
sdr.sample_rate = SAMPLE_RATE
sdr.gain = GAIN

print("📡 Scan PMR446 en cours... (Ctrl+C pour arrêter)")

try:
    while True:
        for channel, freq in PMR_CHANNELS.items():
            sdr.center_freq = freq
            samples = sdr.read_samples(SAMPLES)

            power = 10 * np.log10(np.mean(np.abs(samples)**2))

            if power > THRESHOLD_DB:
                print(f"🔊 Signal détecté sur canal {channel} ({freq/1e6:.5f} MHz) | {power:.1f} dB")

            time.sleep(0.05)

except KeyboardInterrupt:
    print("\n⏹️ Arrêt du scan")
finally:
    sdr.close()
