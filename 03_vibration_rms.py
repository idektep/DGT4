import numpy as np
import matplotlib.pyplot as plt

np.random.seed(0)

# Generate vibration signal
vibration = np.random.normal(0, 1, 1000)

# Inject fault zone
vibration[400:450] += 5

WINDOW = 50
rms = []

# ===============================
# RMS Calculation
# ===============================
for i in range(len(vibration) - WINDOW):
    segment = vibration[i:i+WINDOW]
    rms_value = np.sqrt(np.mean(segment**2))
    rms.append(rms_value)

rms = np.array(rms)

# ===============================
# Fault Threshold
# ===============================
threshold = np.mean(rms) + 2 * np.std(rms)
fault_idx = np.where(rms > threshold)[0]

print("Fault detected at index:", fault_idx[:20])

# ===============================
# Plot
# ===============================
plt.figure(figsize=(12, 5))
plt.plot(rms, label="RMS")
plt.axhline(threshold, color="red", linestyle="--", label="Threshold")
plt.scatter(fault_idx, rms[fault_idx], color="orange", label="Fault")
plt.legend()
plt.title("Vibration RMS Fault Detection")
plt.show()