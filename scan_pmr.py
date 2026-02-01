import numpy as np
import time
from datetime import datetime
from rtlsdr import RtlSdr
from scipy.signal import firwin, lfilter

# === Canaux PMR446 (MHz) ===
PMR_CHANNELS = [
    446.00625e6, 446.01875e6, 446.03125e6, 446.04375e6,
    446.05625e6, 446.06875e6, 446.08125e6, 446.09375e6,
    446.10625e6, 446.11875e6, 446.13125e6, 446.14375e6,
    446.15625e6, 446.16875e6, 446.18125e6, 446.19375e6,
]

# === Paramètres SDR ===
SAMPLE_RATE = 240_000
FFT_SIZE = 2048
CALIBRATION_SAMPLES = 15
THRESHOLD_MARGIN_DB = 20
READS_PER_CHANNEL = 3
HOLD_DURATION = 1.5
DOMINANCE_DB = 5
BW_HZ = 6_000

# === Initialisation SDR ===
sdr = RtlSdr()
sdr.sample_rate = SAMPLE_RATE
sdr.gain = 'auto'

def peak_db(samples):
    spectrum = np.abs(np.fft.fftshift(np.fft.fft(samples)))**2
    spectrum_db = 10 * np.log10(spectrum + 1e-12)
    return np.max(spectrum_db)

def bandpass_filter(samples, fs, bw=BW_HZ):
    nyq = fs / 2
    low = max(0.0001, (0 - bw)/nyq)
    high = min(0.9999, (0 + bw)/nyq)
    b = firwin(101, [low, high], pass_zero=False)
    return lfilter(b, 1.0, samples)

# === Calibration bruit par canal ===
print("⚙️ Calibration du bruit sur tous les canaux (restez silencieux)...")
noise_levels = []
for idx, freq in enumerate(PMR_CHANNELS, start=1):
    sdr.center_freq = freq
    peaks = []
    for _ in range(CALIBRATION_SAMPLES):
        samples = sdr.read_samples(FFT_SIZE)
        filtered = bandpass_filter(samples, SAMPLE_RATE, BW_HZ)
        peaks.append(peak_db(filtered))
        time.sleep(0.05)
    noise_avg = np.mean(peaks)
    noise_levels.append(noise_avg)
    print(f"Canal {idx:02d} | Bruit moyen : {noise_avg:.1f} dB")

thresholds = [nl + THRESHOLD_MARGIN_DB for nl in noise_levels]

print("\n✅ Calibration terminée. Seuils automatiques calculés.")
print("📡 Scanner PMR446 en temps réel (Ctrl+C pour arrêter)...\n")

last_active_channel = None
last_active_time = 0

try:
    while True:
        avg_peaks = []

        # Mesure pour chaque canal
        for idx, freq in enumerate(PMR_CHANNELS):
            sdr.center_freq = freq
            peaks = []
            for _ in range(READS_PER_CHANNEL):
                samples = sdr.read_samples(FFT_SIZE)
                filtered = bandpass_filter(samples, SAMPLE_RATE, BW_HZ)
                peaks.append(peak_db(filtered))
            avg_peaks.append(np.mean(peaks))

        # Détection du canal dominant
        dominant_idx = np.argmax(avg_peaks)
        dominant_peak = avg_peaks[dominant_idx]
        is_dominant = all(dominant_peak - p >= DOMINANCE_DB for i, p in enumerate(avg_peaks) if i != dominant_idx)

        current_time = time.time()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if dominant_peak > thresholds[dominant_idx] and is_dominant:
            # Nouveau canal détecté ?
            if last_active_channel != dominant_idx:
                print(f"{timestamp} | 📢 Canal détecté : {dominant_idx+1} "
                      f"({PMR_CHANNELS[dominant_idx]/1e6:.5f} MHz) | "
                      f"Pic : {avg_peaks[dominant_idx]:.1f} dB")
            last_active_channel = dominant_idx
            last_active_time = current_time
        else:
            if last_active_channel is not None and current_time - last_active_time > HOLD_DURATION:
                last_active_channel = None

        # Affichage canal actif en temps réel
        if last_active_channel is not None:
            print(
                f"📢 Canal actif : {last_active_channel+1} "
                f"({PMR_CHANNELS[last_active_channel]/1e6:.5f} MHz) | "
                f"Pic : {avg_peaks[last_active_channel]:.1f} dB     ",
                end="\r"
            )
        else:
            print("🔇 Aucun canal actif                        ", end="\r")

        time.sleep(0.1)

except KeyboardInterrupt:
    print("\n⛔ Scan arrêté")

finally:
    sdr.close()
