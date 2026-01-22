using UnityEngine;

public class VibrationShakeMQTT : MonoBehaviour
{
    [Header("MQTT")]
    public MQTTCore mqtt;                      // ลาก MQTTCore มาใส่
    public string topicAlert = "dgt/bangkok/zone1/alert";

    [Header("Target Object")]
    public Transform target;                  // Object ที่จะเขย่า

    [Header("Shake Settings")]
    public float riskAmount = 0.03f;
    public float warningAmount = 0.06f;
    public float criticalAmount = 0.1f;
    public float shakeSpeed = 25f;

    Vector3 startPos;
    bool shaking = false;
    float currentAmount = 0f;

    void Start()
    {
        if (target)
            startPos = target.localPosition;
    }

    void OnEnable()
    {
        MQTTCore.OnConnected += OnMQTTConnected;
        MQTTCore.OnMessageReceived += OnMQTT;
    }

    void OnDisable()
    {
        MQTTCore.OnConnected -= OnMQTTConnected;
        MQTTCore.OnMessageReceived -= OnMQTT;
    }

    void OnMQTTConnected()
    {
        if (mqtt)
        {
            mqtt.Subscribe(topicAlert);
            Debug.Log($"[VibrationShakeMQTT] Subscribed: {topicAlert}");
        }
    }

    void OnMQTT(string topic, string msg)
    {
        if (topic != topicAlert) return;

        UnityMainThreadDispatcher.Instance.Enqueue(() =>
        {
            SetAlert(msg);
        });
    }

    void SetAlert(string alert)
    {
        if (!target) return;

        if (alert == "risk")
        {
            currentAmount = riskAmount;
            shaking = true;
        }
        else if (alert == "warning")
        {
            currentAmount = warningAmount;
            shaking = true;
        }
        else if (alert == "critical")
        {
            currentAmount = criticalAmount;
            shaking = true;
        }
        else
        {
            shaking = false;
            target.localPosition = startPos;
        }
    }

    void Update()
    {
        if (!shaking || !target) return;

        float x = Mathf.Sin(Time.time * shakeSpeed) * currentAmount;
        float z = Mathf.Cos(Time.time * shakeSpeed) * currentAmount;

        target.localPosition = startPos + new Vector3(x, 0, z);
    }
}
