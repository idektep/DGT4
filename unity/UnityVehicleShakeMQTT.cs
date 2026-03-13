using UnityEngine;

public class UnityVehicleShakeMQTT : MonoBehaviour
{
    [Header("MQTT")]
    public MQTTCore mqtt;
    public string topicShakeScore = "idt/vehicle/score/shake";

    [Header("Target Object")]
    public Transform target;

    [Header("Shake Settings")]
    public float minShake = 0f;
    public float maxShake = 0.08f;
    public float shakeSpeed = 25f;

    private Vector3 startPos;
    private float currentShakeAmount = 0f;

    void Start()
    {
        if (target == null)
            target = transform;

        startPos = target.localPosition;
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
            mqtt.Subscribe(topicShakeScore);
    }

    void OnMQTTMessage(string t, string msg)
    {
        if (t != topicShakeScore) return;

        if (float.TryParse(msg, out float score))
        {
            UnityMainThreadDispatcher.Instance.Enqueue(() =>
            {
                currentShakeAmount = Mathf.Lerp(minShake, maxShake, score / 100f);
            });
        }
    }

    void Update()
    {
        if (target == null) return;

        if (currentShakeAmount <= 0.0001f)
        {
            target.localPosition = startPos;
            return;
        }

        float x = Mathf.Sin(Time.time * shakeSpeed) * currentShakeAmount;
        float z = Mathf.Cos(Time.time * shakeSpeed) * currentShakeAmount;

        target.localPosition = startPos + new Vector3(x, 0f, z);
    }
}