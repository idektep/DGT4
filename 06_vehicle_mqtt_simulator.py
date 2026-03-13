import math
import random
import time
import paho.mqtt.client as mqtt

BROKER = "broker.emqx.io"
PORT = 1883
BASE_TOPIC = "idt/vehicle"

PUBLISH_INTERVAL = 1.0

random.seed(42)


def simulate_vehicle(step: int) -> dict:
    # speed แบบ smooth
    speed = 70 + 35 * math.sin(step * 0.08) + random.uniform(-4, 4)
    speed = max(0, speed)

    # steering ซ้ายขวาแบบ smooth
    steering = 20 * math.sin(step * 0.05) + random.uniform(-2, 2)

    # outside temperature
    outside_temp = 30 + 3 * math.sin(step * 0.03) + random.uniform(-0.5, 0.5)

    # cabin temperature
    cabin_temp = outside_temp + 2 + 1.2 * math.sin(step * 0.04) + random.uniform(-0.4, 0.4)

    # engine temperature ขึ้นกับ speed
    engine_temp = 72 + speed * 0.22 + random.uniform(-1.5, 1.5)

    # tire temperature ขึ้นกับ speed
    tire_temp = 30 + speed * 0.18 + random.uniform(-1.0, 1.0)

    # vibration ขึ้นกับ speed
    vibration = 0.6 + speed / 90.0 + random.uniform(-0.15, 0.15)

    # following distance
    distance = 55 + 18 * math.sin(step * 0.11 + 1.0) + random.uniform(-4, 4)
    distance = max(3, distance)

    # abnormal scenarios
    if 35 <= step % 120 <= 45:
        engine_temp += 12

    if 60 <= step % 120 <= 70:
        tire_temp += 8

    if 80 <= step % 120 <= 85:
        cabin_temp += 6

    if 90 <= step % 120 <= 100:
        vibration += 2.5

    if 105 <= step % 120 <= 112:
        distance -= 25

    return {
        "speed": round(speed, 2),
        "steering": round(steering, 2),
        "outside_temp": round(outside_temp, 2),
        "cabin_temp": round(cabin_temp, 2),
        "engine_temp": round(engine_temp, 2),
        "tire_temp": round(tire_temp, 2),
        "vibration": round(vibration, 3),
        "distance": round(distance, 2),
    }


def publish_state(client: mqtt.Client, state: dict):
    for key, value in state.items():
        topic = f"{BASE_TOPIC}/state/{key}"
        client.publish(topic, str(value))


def main():
    client = mqtt.Client()
    client.connect(BROKER, PORT, 60)
    client.loop_start()

    print("Vehicle MQTT simulator started")
    print(f"Topic prefix: {BASE_TOPIC}/state/")

    step = 0
    try:
        while True:
            state = simulate_vehicle(step)
            publish_state(client, state)
            print(state)

            step += 1
            time.sleep(PUBLISH_INTERVAL)

    except KeyboardInterrupt:
        print("Stopping simulator...")

    finally:
        client.loop_stop()
        client.disconnect()


if __name__ == "__main__":
    main()