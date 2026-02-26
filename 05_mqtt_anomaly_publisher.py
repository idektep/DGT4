import numpy as np
import time
import paho.mqtt.client as mqtt

# MQTT Setup
BROKER = "broker.emqx.io"
TOPIC = "dgt/factory/zone1/temp_anomaly"

client = mqtt.Client()
client.connect(BROKER, 1883, 60)
client.loop_start()

mean = 50
std = 3

window = []
WINDOW_SIZE = 10
K = 2.0

print("MQTT Anomaly Detection Running...\n")

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
                print("ANOMALY:", temp)
                client.publish(TOPIC, "1")
            else:
                client.publish(TOPIC, "0")

    time.sleep(2)