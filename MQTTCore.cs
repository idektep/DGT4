using UnityEngine;
using System;
using System.Text;
using System.Collections;
using uPLibrary.Networking.M2Mqtt;
using uPLibrary.Networking.M2Mqtt.Messages;

public class MQTTCore : MonoBehaviour
{
    [Header("MQTT Settings")]
    public string broker = "broker.emqx.io";
    public int port = 1883;
    public bool autoReconnect = true;
    public float reconnectDelay = 3f;

    private MqttClient client;
    private string clientId;
    private bool isConnecting = false;

    public static event Action<string, string> OnMessageReceived;
    public static event Action OnConnected;

    void Start()
    {
        Connect();
    }

    void Connect()
    {
        if (isConnecting) return;
        isConnecting = true;

        try
        {
            clientId = "unity_" + Guid.NewGuid().ToString("N").Substring(0, 8);
            client = new MqttClient(broker);

            client.MqttMsgPublishReceived += OnMQTTMessage;
            client.ConnectionClosed += OnConnectionClosed;

            client.Connect(clientId);

            Debug.Log($"🟢 MQTT Connected as {clientId}");
            isConnecting = false;

            OnConnected?.Invoke();   // แจ้งทุก Controller ว่าพร้อมแล้ว
        }
        catch (Exception ex)
        {
            Debug.LogWarning($"⚠️ MQTT Connect failed: {ex.Message}");
            isConnecting = false;

            if (autoReconnect)
                StartCoroutine(Reconnect());
        }
    }

    void OnConnectionClosed(object sender, EventArgs e)
    {
        Debug.LogWarning("❌ MQTT Disconnected!");
        if (autoReconnect)
            StartCoroutine(Reconnect());
    }

    IEnumerator Reconnect()
    {
        yield return new WaitForSeconds(reconnectDelay);
        Connect();
    }

    void OnMQTTMessage(object sender, MqttMsgPublishEventArgs e)
    {
        string topic = e.Topic;
        string message = Encoding.UTF8.GetString(e.Message);

        Debug.Log($"📥 MQTT Message: [{topic}] {message}");
        OnMessageReceived?.Invoke(topic, message);
    }

    public void Subscribe(string topic)
    {
        if (client != null && client.IsConnected)
        {
            client.Subscribe(
                new string[] { topic },
                new byte[] { MqttMsgBase.QOS_LEVEL_AT_LEAST_ONCE }
            );

            Debug.Log($"📡 Subscribed: {topic}");
        }
        else
        {
            Debug.LogWarning("❌ MQTT not connected (Subscribe failed)");
        }
    }

    public void Publish(string topic, string message)
    {
        if (client != null && client.IsConnected)
        {
            client.Publish(topic, Encoding.UTF8.GetBytes(message));
        }
        else
        {
            Debug.LogWarning("❌ MQTT not connected (Publish failed)");
        }
    }
}
