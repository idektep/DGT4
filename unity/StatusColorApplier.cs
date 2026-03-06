using System;
using UnityEngine;

public class StatusColorApplier : MonoBehaviour
{
    [Header("MQTT Core")]
    public MQTTCore mqtt;

    [Header("Topics")]
    public string topicState = "dt/vision/person1/state";
    public string topicEvent = "dt/vision/person1/event";

    [Header("Renderer")]
    public Renderer targetRenderer;

    [Header("Colors")]
    public Color standing = Color.green;
    public Color lying = Color.gray;
    public Color falling = Color.yellow;
    public Color cooldown = Color.cyan;
    public Color alarmRed = Color.red;
    public Color unknown = Color.white;

    [Header("Fall latch")]
    public float alarmLatchSec = 3.0f;

    [Serializable] public class StateMsg { public double ts; public string id; public string state; }
    [Serializable] public class EventMsg { public double ts; public string id; public string eventName; }

    private string lastState = "UNKNOWN";
    private float alarmUntil = 0f;

    void Start()
    {
        if (mqtt == null) mqtt = FindObjectOfType<MQTTCore>();
        if (mqtt == null)
        {
            Debug.LogError("StatusColorApplier: ไม่พบ MQTTCore ใน Scene");
            return;
        }

        if (targetRenderer == null) targetRenderer = GetComponent<Renderer>();

        MQTTCore.OnMessageReceived += HandleMessage;
        MQTTCore.OnConnected += HandleConnected;

        // ลอง subscribe ตอนเริ่ม
        mqtt.Subscribe(topicState);
        mqtt.Subscribe(topicEvent);
    }

    void HandleConnected()
    {
        // subscribe ซ้ำตอน connect สำเร็จ
        if (mqtt == null) return;
        mqtt.Subscribe(topicState);
        mqtt.Subscribe(topicEvent);
    }

    void HandleMessage(string topic, string payload)
    {
        if (topic == topicState)
        {
            var s = JsonUtility.FromJson<StateMsg>(payload);
            if (s != null && !string.IsNullOrEmpty(s.state))
                lastState = s.state;
        }
        else if (topic == topicEvent)
        {
            var e = JsonUtility.FromJson<EventMsg>(payload);
            if (e != null && e.eventName == "FALL")
                alarmUntil = Time.time + alarmLatchSec;
        }
    }

    void Update()
    {
        if (targetRenderer == null) return;

        if (Time.time < alarmUntil)
        {
            targetRenderer.material.color = alarmRed;
            return;
        }

        targetRenderer.material.color = lastState switch
        {
            "STANDING" => standing,
            "LYING" => lying,
            "FALLING" => falling,
            "COOLDOWN" => cooldown,
            _ => unknown
        };
    }

    void OnDestroy()
    {
        MQTTCore.OnMessageReceived -= HandleMessage;
        MQTTCore.OnConnected -= HandleConnected;
    }
}