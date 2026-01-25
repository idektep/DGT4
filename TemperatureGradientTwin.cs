using UnityEngine;

public class TemperatureGradientTwin : MonoBehaviour
{
    [Header("MQTT")]
    public MQTTCore mqtt;
    public string topic = "idt/sensor/temp";

    [Header("Temperature Range")]
    public float minTemp = 25f;
    public float maxTemp = 50f;

    [Header("Color Gradient")]
    public Gradient temperatureGradient;

    private Renderer rend;

    void Start()
    {
        rend = GetComponent<Renderer>();
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
        mqtt.Subscribe(topic);
    }

    void OnMQTTMessage(string t, string msg)
    {
        if (t != topic) return;

        if (float.TryParse(msg, out float temp))
        {
            UnityMainThreadDispatcher.Instance.Enqueue(() =>
            {
                UpdateColor(temp);
            });
        }
    }

    void UpdateColor(float temp)
    {
        // map temp → 0..1
        float t = Mathf.InverseLerp(minTemp, maxTemp, temp);

        // evaluate gradient
        Color color = temperatureGradient.Evaluate(t);

        rend.material.color = color;
    }
}
