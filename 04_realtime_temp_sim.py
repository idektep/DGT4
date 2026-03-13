import numpy as np
import time

mean = 50
std = 3

window = []
WINDOW_SIZE = 10
K = 2.0

print("Starting Real-time Simulation...\n")

while True:
    temp = np.random.normal(mean, std)

    window.append(temp)

    if len(window) > WINDOW_SIZE:
        window.pop(0)

    if len(window) == WINDOW_SIZE:
        rolling_mean = np.mean(window)
        rolling_std = np.std(window)

        if rolling_std > 0:
            if abs(temp - rolling_mean) > K * rolling_std:
                print("ALERT! Temp anomaly:", temp)
            else:
                print("Normal:", temp)
    else:
        print("Collecting baseline:", temp)

    time.sleep(2)