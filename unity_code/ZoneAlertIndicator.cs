using UnityEngine;

public class ZoneAlertIndicator : MonoBehaviour
{
    [Header("MQTT")]
    public MQTTCore mqtt;              // ลาก MQTTCore มาใส่
    public string topicAlert = "dgt/bangkok/zone1/alert";

    [Header("Indicator Renderer")]
    public Renderer indicatorRenderer;

    [Header("Colors")]
    public Color normalColor = Color.green;
    public Color alertColor  = Color.red;

    void Start()
    {
        SetAlert("normal");
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
            Debug.Log($"[ZoneAlertIndicator] Subscribed: {topicAlert}");
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

    public void SetAlert(string alert)
    {
        if (!indicatorRenderer) return;

        bool isAlert =
            alert == "risk" ||
            alert == "warning" ||
            alert == "critical";

        indicatorRenderer.material.color =
            isAlert ? alertColor : normalColor;
    }
}
