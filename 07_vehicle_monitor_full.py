import time
from collections import deque
import numpy as np
import paho.mqtt.client as mqtt

# =========================================================
# MQTT CONFIG
# =========================================================
BROKER = "broker.emqx.io"
PORT = 1883
BASE_TOPIC = "idt/vehicle"

STATE_TOPIC = f"{BASE_TOPIC}/state/+"
SCORE_TOPIC = f"{BASE_TOPIC}/score"
STATUS_TOPIC = f"{BASE_TOPIC}/status"

# =========================================================
# ANALYSIS CONFIG
# =========================================================
ROLLING_WINDOW = 12
ROLLING_K = 2.2

VIB_RAW_WINDOW = 20
VIB_RMS_HISTORY = 20
VIB_K = 2.0

SAFE_DISTANCE_FACTOR = 0.5

# =========================================================
# LATEST STATE STORAGE
# =========================================================
latest_state = {
    "speed": None,
    "steering": None,
    "outside_temp": None,
    "cabin_temp": None,
    "engine_temp": None,
    "tire_temp": None,
    "vibration": None,
    "distance": None,
}

# rolling windows for anomaly detection
cabin_window = deque(maxlen=ROLLING_WINDOW)
engine_window = deque(maxlen=ROLLING_WINDOW)
tire_residual_window = deque(maxlen=ROLLING_WINDOW)

# vibration windows
vibration_raw_window = deque(maxlen=VIB_RAW_WINDOW)
vibration_rms_history = deque(maxlen=VIB_RMS_HISTORY)


def parse_value(payload: bytes):
    text = payload.decode("utf-8").strip()
    try:
        return float(text)
    except ValueError:
        return text


def clamp_0_100(x: float) -> float:
    return max(0.0, min(100.0, x))


def map_range(value: float, in_min: float, in_max: float) -> float:
    """
    map value from [in_min, in_max] to [0,100]
    """
    if in_max <= in_min:
        return 0.0
    t = (value - in_min) / (in_max - in_min)
    return clamp_0_100(t * 100.0)


def rolling_anomaly_score(value: float, window: deque, threshold_k: float):
    """
    Return:
    is_anomaly, mean, std, score_0_100
    """
    window.append(value)

    if len(window) < window.maxlen:
        return False, None, None, 0.0

    arr = np.array(window, dtype=float)
    mean = arr.mean()
    std = arr.std()

    if std <= 1e-9:
        return False, mean, std, 0.0

    z = abs(value - mean) / std
    is_anomaly = z > threshold_k

    # threshold_k เริ่มเป็น 0 คะแนน
    # threshold_k + 3 เริ่มเข้าใกล้ 100 คะแนน
    score = clamp_0_100(((z - threshold_k) / 3.0) * 100.0)
    return is_anomaly, mean, std, score


def rms(values) -> float:
    arr = np.array(values, dtype=float)
    return float(np.sqrt(np.mean(arr ** 2)))


def vibration_anomaly_score(vibration_value: float):
    """
    Return:
    is_anomaly, current_rms, mean, std, score_0_100
    """
    vibration_raw_window.append(vibration_value)

    if len(vibration_raw_window) < vibration_raw_window.maxlen:
        return False, None, None, None, 0.0

    current_rms = rms(vibration_raw_window)
    vibration_rms_history.append(current_rms)

    if len(vibration_rms_history) < vibration_rms_history.maxlen:
        return False, current_rms, None, None, 0.0

    arr = np.array(vibration_rms_history, dtype=float)
    mean = arr.mean()
    std = arr.std()

    if std <= 1e-9:
        return False, current_rms, mean, std, 0.0

    z = abs(current_rms - mean) / std
    is_anomaly = z > VIB_K
    score = clamp_0_100(((z - VIB_K) / 3.0) * 100.0)

    return is_anomaly, current_rms, mean, std, score


def tire_expected_from_speed(speed: float) -> float:
    """
    expected tire temperature from vehicle speed
    """
    return 30.0 + speed * 0.18


def distance_risk_score(speed: float, distance: float):
    """
    Return:
    score_0_100, status_string, safe_distance
    """
    safe_distance = speed * SAFE_DISTANCE_FACTOR

    if safe_distance <= 1e-9:
        return 0.0, "normal", safe_distance

    ratio = distance / safe_distance

    if ratio < 0.6:
        return 100.0, "danger", safe_distance
    elif ratio < 1.0:
        # ยิ่งใกล้ 0.6 ยิ่งคะแนนสูง
        score = map_range(1.0 - ratio, 0.0, 0.4)
        return score, "warning", safe_distance
    else:
        return 0.0, "normal", safe_distance


def overall_status_from_scores(scores: dict) -> str:
    max_score = max(scores.values())

    if max_score >= 80:
        return "danger"
    elif max_score >= 40:
        return "warning"
    return "normal"


def publish_dict(client: mqtt.Client, topic_prefix: str, data: dict):
    for key, value in data.items():
        if isinstance(value, float):
            client.publish(f"{topic_prefix}/{key}", f"{value:.2f}")
        else:
            client.publish(f"{topic_prefix}/{key}", str(value))


def state_ready() -> bool:
    return all(value is not None for value in latest_state.values())


# =========================================================
# MAIN ANALYSIS
# =========================================================
def analyze_and_publish(client: mqtt.Client):
    if not state_ready():
        return

    speed = float(latest_state["speed"])
    steering = float(latest_state["steering"])
    outside_temp = float(latest_state["outside_temp"])
    cabin_temp = float(latest_state["cabin_temp"])
    engine_temp = float(latest_state["engine_temp"])
    tire_temp = float(latest_state["tire_temp"])
    vibration = float(latest_state["vibration"])
    distance = float(latest_state["distance"])

    # -----------------------------------------------------
    # BASE SCORES (direct mapping)
    # -----------------------------------------------------
    body_score = map_range(outside_temp, 26.0, 38.0)
    glass_base_score = map_range(cabin_temp, 28.0, 42.0)
    hood_base_score = map_range(engine_temp, 70.0, 120.0)

    tire_expected = tire_expected_from_speed(speed)
    tire_residual = tire_temp - tire_expected
    wheel_base_score = map_range(tire_residual, 0.0, 12.0)

    bumper_score, distance_status, safe_distance = distance_risk_score(speed, distance)
    shake_base_score = map_range(vibration, 0.5, 4.0)

    # -----------------------------------------------------
    # ANOMALY SCORES
    # -----------------------------------------------------
    cabin_is_anom, cabin_mean, cabin_std, glass_anomaly_score = rolling_anomaly_score(
        cabin_temp, cabin_window, ROLLING_K
    )

    engine_is_anom, engine_mean, engine_std, hood_anomaly_score = rolling_anomaly_score(
        engine_temp, engine_window, ROLLING_K
    )

    tire_is_anom, tire_mean, tire_std, wheel_anomaly_score = rolling_anomaly_score(
        tire_residual, tire_residual_window, ROLLING_K
    )

    vib_is_anom, vib_rms, vib_mean, vib_std, shake_anomaly_score = vibration_anomaly_score(
        vibration
    )

    # -----------------------------------------------------
    # MERGE BASE + ANOMALY
    # -----------------------------------------------------
    glass_score = clamp_0_100(max(glass_base_score, glass_anomaly_score))
    hood_score = clamp_0_100(max(hood_base_score, hood_anomaly_score))
    wheel_score = clamp_0_100(max(wheel_base_score, wheel_anomaly_score))
    shake_score = clamp_0_100(max(shake_base_score, shake_anomaly_score))

    scores = {
        "body": body_score,
        "glass": glass_score,
        "hood": hood_score,
        "wheel": wheel_score,
        "shake": shake_score,
        "bumper": bumper_score,
    }

    vibration_status = overall_status_from_scores({"shake": shake_score})
    overall_status = overall_status_from_scores(scores)

    status = {
        "distance": distance_status,
        "vibration": vibration_status,
        "overall": overall_status,
    }

    debug_info = {
        "speed": round(speed, 2),
        "steering": round(steering, 2),
        "outside_temp": round(outside_temp, 2),
        "cabin_temp": round(cabin_temp, 2),
        "engine_temp": round(engine_temp, 2),
        "tire_temp": round(tire_temp, 2),
        "vibration": round(vibration, 3),
        "distance": round(distance, 2),
        "safe_distance": round(safe_distance, 2),
        "tire_expected": round(tire_expected, 2),
        "tire_residual": round(tire_residual, 2),
        "cabin_anomaly": int(cabin_is_anom),
        "engine_anomaly": int(engine_is_anom),
        "tire_anomaly": int(tire_is_anom),
        "vibration_anomaly": int(vib_is_anom) if vib_rms is not None else 0,
        "cabin_mean": None if cabin_mean is None else round(cabin_mean, 2),
        "engine_mean": None if engine_mean is None else round(engine_mean, 2),
        "tire_mean": None if tire_mean is None else round(tire_mean, 2),
        "vibration_rms": None if vib_rms is None else round(vib_rms, 3),
    }

    publish_dict(client, SCORE_TOPIC, scores)
    publish_dict(client, STATUS_TOPIC, status)

    print("STATE  :", {k: round(v, 2) if isinstance(v, float) else v for k, v in latest_state.items()})
    print("SCORE  :", {k: round(v, 2) for k, v in scores.items()})
    print("STATUS :", status)
    print("DEBUG  :", debug_info)
    print("-" * 80)


# =========================================================
# MQTT CALLBACKS
# =========================================================
def on_connect(client, userdata, flags, rc):
    print("Connected:", rc)
    client.subscribe(STATE_TOPIC)
    print("Subscribed to:", STATE_TOPIC)


def on_message(client, userdata, msg):
    key = msg.topic.split("/")[-1]
    value = parse_value(msg.payload)

    if key in latest_state:
        latest_state[key] = value

    analyze_and_publish(client)


# =========================================================
# MAIN
# =========================================================
def main():
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    client.connect(BROKER, PORT, 60)
    client.loop_start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping full monitor...")
    finally:
        client.loop_stop()
        client.disconnect()


if __name__ == "__main__":
    main()