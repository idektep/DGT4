using UnityEngine;

public class UnityVehicleSteeringMQTT : MonoBehaviour
{
    [Header("MQTT")]
    public MQTTCore mqtt;
    public string topicSteering = "idt/vehicle/state/steering";

    [Header("Steering Settings")]
    public bool invertSteering = false;
    public float steeringOffset = 0f;
    public float rotationSpeed = 180f;
    public Vector3 steeringAxis = Vector3.up;

    private float targetAngle = 0f;
    private Quaternion initialRotation;

    void Start()
    {
        initialRotation = transform.localRotation;
    }

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
            mqtt.Subscribe(topicSteering);
    }

    void OnMQTTMessage(string t, string msg)
    {
        if (t != topicSteering) return;

        if (float.TryParse(msg, out float steering))
        {
            UnityMainThreadDispatcher.Instance.Enqueue(() =>
            {
                targetAngle = steering;
            });
        }
    }

    void Update()
    {
        float angle = (invertSteering ? -targetAngle : targetAngle) + steeringOffset;
        Quaternion targetRot = initialRotation * Quaternion.AngleAxis(angle, steeringAxis);
        transform.localRotation = Quaternion.RotateTowards(
            transform.localRotation,
            targetRot,
            rotationSpeed * Time.deltaTime
        );
    }
}