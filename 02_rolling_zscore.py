import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

np.random.seed(0)

# Generate data with slight trend
data = np.random.normal(50, 3, 300)
data += np.linspace(0, 5, 300)

# Inject anomaly
data[150] = 80

df = pd.DataFrame({"temp": data})

# ===============================
# Rolling parameters
# ===============================
WINDOW = 15
K = 2.0

df["rolling_mean"] = df["temp"].rolling(window=WINDOW).mean()
df["rolling_std"] = df["temp"].rolling(window=WINDOW).std()

df["anomaly"] = (
    abs(df["temp"] - df["rolling_mean"]) > K * df["rolling_std"]
)

# ===============================
# Plot
# ===============================
plt.figure(figsize=(12,5))
plt.plot(df["temp"], label="Temperature")
plt.plot(df["rolling_mean"], label="Rolling Mean")
plt.scatter(
    df.index[df["anomaly"]],
    df["temp"][df["anomaly"]],
    color='red',
    label="Anomaly"
)
plt.legend()
plt.title("Rolling Window Z-Score Detection")
plt.show()