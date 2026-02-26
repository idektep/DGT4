import numpy as np
import matplotlib.pyplot as plt

# ===============================
# STEP 1: Generate Temperature Data
# ===============================

np.random.seed(0)

# Normal temp distribution (mean=50, std=3)
data = np.random.normal(50, 3, 200)

# Inject anomalies
data[50] = 80
data[120] = 20

# ===============================
# STEP 2: Compute Mean & Std
# ===============================

mean = np.mean(data)
std = np.std(data)

print("Mean:", mean)
print("Std:", std)

# ===============================
# STEP 3: Compute Z-score
# ===============================

z_scores = (data - mean) / std

# Threshold selection
Z_THRESHOLD = 2.5

anomaly_idx = np.where(np.abs(z_scores) > Z_THRESHOLD)[0]

print("Anomaly Index:", anomaly_idx)

# ===============================
# STEP 4: Plot Results
# ===============================

plt.figure(figsize=(10,4))
plt.plot(data, label="Temperature")
plt.scatter(anomaly_idx, data[anomaly_idx], color='red', label="Anomaly")
plt.axhline(mean, color='green', linestyle='--', label="Mean")
plt.legend()
plt.title("Global Z-Score Anomaly Detection")
plt.show()