using UnityEngine;

public class LightControl : MonoBehaviour
{
    [Header("MQTT Reference")]
    public MQTTCore mqtt;   // 👈 จะขึ้นใน Inspector แน่นอน

    [Header("MQTT Topic")]
    public string lightStatusTopic = "dgt/light/status";

    [Header("Light")]
    public Light targetLight;

    [Header("Material")]
    public Renderer lampRenderer;
    public Color onColor = Color.yellow;
    public Color offColor = Color.gray;

    private bool lightState = false;

    void OnEnable()
    {
        MQTTCore.OnConnected += OnMQTTConnected;
        MQTTCore.OnMessageReceived += HandleMQTT;
    }

    void OnDisable()
    {
        MQTTCore.OnConnected -= OnMQTTConnected;
        MQTTCore.OnMessageReceived -= HandleMQTT;
    }

    void OnMQTTConnected()
    {
        if (mqtt == null) return;

        mqtt.Subscribe(lightStatusTopic);
        Debug.Log($"🛰 Subscribed: {lightStatusTopic}");
    }

    void HandleMQTT(string topic, string msg)
    {
        if (topic != lightStatusTopic) return;

        UnityMainThreadDispatcher.Instance.Enqueue(() =>
        {
            if (msg == "on") SetLight(true);
            else if (msg == "off") SetLight(false);
        });
    }

    void SetLight(bool state)
    {
        lightState = state;

        if (targetLight)
            targetLight.enabled = lightState;

        if (lampRenderer)
            lampRenderer.material.color = lightState ? onColor : offColor;

        Debug.Log($"💡 Light = {(lightState ? "ON" : "OFF")}");
    }
}
