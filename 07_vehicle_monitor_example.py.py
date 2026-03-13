import numpy as np
from collections import deque
import paho.mqtt.client as mqtt

BROKER = "broker.emqx.io"
PORT = 1883

# -------- topic --------
SUB_TOPIC = "idt/vehicle/state/cabin_temp"
PUB_TOPIC = "idt/vehicle/score/glass"

# -------- anomaly config --------
WINDOW = 12
Z_THRESHOLD = 2.2

history = deque(maxlen=WINDOW)


def clamp_0_100(x):
    return max(0.0, min(100.0, x))


def map_range(value, min_v, max_v):
    """
    แปลงค่า sensor -> score 0-100
    """
    if max_v <= min_v:
        return 0.0
    t = (value - min_v) / (max_v - min_v)
    return clamp_0_100(t * 100.0)


def rolling_z_score(value):
    """
    anomaly detection แบบ rolling z-score
    คืนเป็น anomaly score 0-100
    """
    history.append(value)

    if len(history) < WINDOW:
        return 0.0

    arr = np.array(history, dtype=float)

    mean = arr.mean()
    std = arr.std()

    if std < 1e-6:
        return 0.0

    z = abs(value - mean) / std

    if z <= Z_THRESHOLD:
        return 0.0

    anomaly_score = ((z - Z_THRESHOLD) / 3.0) * 100.0
    return clamp_0_100(anomaly_score)


def on_connect(client, userdata, flags, rc):
    print("Connected:", rc)
    client.subscribe(SUB_TOPIC)
    print("Subscribe:", SUB_TOPIC)


def on_message(client, userdata, msg):
    text = msg.payload.decode("utf-8").strip()

    try:
        cabin_temp = float(text)
    except ValueError:
        return

    # base score จาก temp
    base_score = map_range(cabin_temp, 28.0, 42.0)

    # anomaly score
    anomaly_score = rolling_z_score(cabin_temp)

    # รวม score
    final_score = max(base_score, anomaly_score)

    client.publish(PUB_TOPIC, f"{final_score:.2f}")

    print(
        "temp:", round(cabin_temp, 2),
        "| base:", round(base_score, 2),
        "| anomaly:", round(anomaly_score, 2),
        "| score:", round(final_score, 2)
    )


def main():
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    client.connect(BROKER, PORT, 60)
    client.loop_forever()


if __name__ == "__main__":
    main()