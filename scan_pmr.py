import numpy as np
import time
from datetime import datetime
from rtlsdr import RtlSdr

# === Canaux PMR446 (MHz) ===
PMR_CHANNELS = [
    446.00625e6, 446.01875e6, 446.03125e6, 446.04375e6,
    446.05625e6, 446.06875e6, 446.08125e6, 446.09375e6,
    446.10625e6, 446.11875e6, 446.13125e6, 446.14375e6,
    446.15625e6, 446.16875e6, 446.18125e6, 446.19375e6,
]

# === Paramètres SDR ===
SAMPLE_RATE = 240_000
FFT_SIZE = 65536
CALIBRATION_SAMPLES = 10
THRESHOLD_MARGIN_DB = 6
HOLD_DURATION = 1.5
CHANNEL_BW = 10e3
HISTORY_LENGTH = 15
HISTORY_MIN_INTERVAL = 1.0
MIN_SIGNAL_MARGIN_DB = 0.5  # Pour filtrer bleed-over

# === Initialisation SDR ===
sdr = RtlSdr()
sdr.sample_rate = SAMPLE_RATE
#sdr.gain = 'auto'
sdr.gain = 50

# === Fonction puissance par canal via FFT ===
def channel_power_db(samples, fs, channel_freq, center_freq, bw=CHANNEL_BW):
    fft = np.fft.fftshift(np.fft.fft(samples, FFT_SIZE))
    freqs = np.fft.fftshift(np.fft.fftfreq(len(samples), 1/fs)) + center_freq
    mask = (freqs >= channel_freq - bw/2) & (freqs <= channel_freq + bw/2)
    power = np.sum(np.abs(fft[mask])**2) / max(np.sum(mask), 1)
    return 10 * np.log10(power + 1e-12)

# === Calibration bruit par canal ===
print("⚙️ Calibration du bruit sur tous les canaux (restez silencieux)...")
noise_levels = []
center_freq = PMR_CHANNELS[len(PMR_CHANNELS)//2]
sdr.center_freq = center_freq

for idx, freq in enumerate(PMR_CHANNELS, start=1):
    peaks = []
    for _ in range(CALIBRATION_SAMPLES):
        samples = sdr.read_samples(FFT_SIZE)
        peaks.append(channel_power_db(samples, SAMPLE_RATE, freq, center_freq))
        time.sleep(0.05)
    noise_avg = np.mean(peaks)
    noise_levels.append(noise_avg)
    print(f"Canal {idx:02d} | Bruit moyen : {noise_avg:.1f} dB")

thresholds = [nl + THRESHOLD_MARGIN_DB for nl in noise_levels]

print("\n✅ Calibration terminée. Scanner en temps réel (Ctrl+C pour arrêter)...\n")

# === Variables de suivi ===
last_active_times = [0] * len(PMR_CHANNELS)
history = []
last_seen = [0] * len(PMR_CHANNELS)

try:
    while True:
        samples = sdr.read_samples(FFT_SIZE)
        current_time = time.time()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        channel_powers = []

        # Calcul puissance de tous les canaux
        for idx, freq in enumerate(PMR_CHANNELS):
            power_db = channel_power_db(samples, SAMPLE_RATE, freq, center_freq)
            channel_powers.append((idx, power_db))

        # Déterminer canal dominant
        dominant_idx, dominant_power = max(channel_powers, key=lambda x: x[1])

        # Vérifier si le canal dominant dépasse le seuil + marge
        active_channels = []
        if dominant_power > thresholds[dominant_idx] + MIN_SIGNAL_MARGIN_DB:
            last_active_times[dominant_idx] = current_time
            active_channels.append((dominant_idx, dominant_power))

            # Historique : ajouter si intervalle respecté
            if current_time - last_seen[dominant_idx] > HISTORY_MIN_INTERVAL:
                history.append((dominant_idx, timestamp))
                last_seen[dominant_idx] = current_time
                if len(history) > HISTORY_LENGTH:
                    history.pop(0)

        # Maintien des canaux actifs pour HOLD_DURATION
        for idx, _ in channel_powers:
            if current_time - last_active_times[idx] <= HOLD_DURATION:
                if idx != dominant_idx:
                    # Ajouter les canaux maintenus (puissance faible)
                    power_db = next(p for i, p in channel_powers if i == idx)
                    active_channels.append((idx, power_db))

        # --- Affichage ---
        print("\033[2J\033[H", end="")  # Clear screen + move cursor top-left

        # Historique
        print("📜 Historique des canaux détectés (derniers):")
        for idx_hist, ts_hist in history:
            print(f"{ts_hist} | Canal {idx_hist+1:02d} ({PMR_CHANNELS[idx_hist]/1e6:.5f} MHz)")

        # Canaux actifs
        print("\n📡 Canaux actifs en temps réel:")
        if active_channels:
            lines = []
            for idx, power_db in active_channels:
                lines.append(
                    f"📢 Canal {idx+1:02d} ({PMR_CHANNELS[idx]/1e6:.5f} MHz) | Puissance : {power_db:.1f} dB"
                )
            print(" | ".join(lines))
        else:
            print("🔇 Aucun canal actif")

        time.sleep(0.1)

except KeyboardInterrupt:
    print("\n⛔ Scan arrêté")

finally:
    sdr.close()
