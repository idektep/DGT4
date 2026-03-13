using UnityEngine;

public class UnityVehicleWheelSpinMQTT : MonoBehaviour
{
    [Header("MQTT")]
    public MQTTCore mqtt;
    public string topicSpeed = "idt/vehicle/state/speed";

    [Header("Spin Settings")]
    public float rpmMultiplier = 8f;
    public Vector3 spinAxis = Vector3.right;
    public bool invertSpinDirection = false;

    private float currentRPM = 0f;

    void OnEnable()
    {
        MQTTCore.OnConnected += OnMQTTConnected;
        MQTTCore.OnMessageReceived += OnMQTTMessage;
    }

    void OnDisable()
    {
        MQTTCore.OnConnected -= OnMQTTConnected;
        MQTTCore.OnMessageReceived -= OnMQTTMessage;
    }

    void OnMQTTConnected()
    {
        if (mqtt != null)
            mqtt.Subscribe(topicSpeed);
    }

    void OnMQTTMessage(string t, string msg)
    {
        if (t != topicSpeed) return;

        if (float.TryParse(msg, out float speed))
        {
            UnityMainThreadDispatcher.Instance.Enqueue(() =>
            {
                currentRPM = speed * rpmMultiplier;
            });
        }
    }

    void Update()
    {
        float direction = invertSpinDirection ? -1f : 1f;
        float degreesPerSecond = currentRPM * 360f / 60f;
        transform.Rotate(spinAxis, degreesPerSecond * Time.deltaTime * direction, Space.Self);
    }
}