using UnityEngine;

public class UnityGradientPartMQTT : MonoBehaviour
{
    [Header("MQTT")]
    public MQTTCore mqtt;
    public string topic = "idt/vehicle/score/body";

    [Header("Target Renderer")]
    public Renderer targetRenderer;

    [Header("Score Range")]
    public float minScore = 0f;
    public float maxScore = 100f;

    [Header("Color Gradient")]
    public Gradient scoreGradient;

    [Header("Optional")]
    public bool useSharedMaterial = false;

    private Material targetMaterial;

    void Start()
    {
        if (targetRenderer == null)
            targetRenderer = GetComponent<Renderer>();

        if (targetRenderer != null)
            targetMaterial = useSharedMaterial ? targetRenderer.sharedMaterial : targetRenderer.material;
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
            mqtt.Subscribe(topic);
    }

    void OnMQTTMessage(string t, string msg)
    {
        if (t != topic) return;

        if (float.TryParse(msg, out float score))
        {
            UnityMainThreadDispatcher.Instance.Enqueue(() =>
            {
                UpdateColor(score);
            });
        }
    }

    public void UpdateColor(float score)
    {
        if (targetMaterial == null) return;

        float t = Mathf.InverseLerp(minScore, maxScore, score);
        Color color = scoreGradient.Evaluate(t);
        targetMaterial.color = color;
    }
}