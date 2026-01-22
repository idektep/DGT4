import paho.mqtt.client as mqtt
from temp_analyzer import TempAnalyzer

# ======================
# CONFIG
# ======================
BROKER = "broker.emqx.io"
TOPIC_IN  = "dgt/bangkok/zone1/temp"
TOPIC_OUT = "dgt/bangkok/zone1/temp/alert"

ZONE_NAME = "bangkok_zone1_temp"

analyzer = TempAnalyzer()

# ======================
def on_connect(client, userdata, flags, rc):
    print(f"[{ZONE_NAME}] MQTT Connected")
    client.subscribe(TOPIC_IN)

def on_message(client, userdata, msg):
    try:
        value = float(msg.payload.decode())
    except:
        print(f"[{ZONE_NAME}] Invalid payload")
        return

    analyzer.update(value)
    alert = analyzer.decide(value)

    print(f"[{ZONE_NAME}] Temp={value:.1f} → {alert}")
    client.publish(TOPIC_OUT, alert)

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

client.connect(BROKER, 1883, 60)
client.loop_forever()
