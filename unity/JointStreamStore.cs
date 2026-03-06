using System;
using System.Collections.Generic;
using UnityEngine;

public class JointStreamStore : MonoBehaviour
{
    [Header("MQTT Core (ลากตัว MQTTCore ใน Scene มาใส่ หรือปล่อยว่างให้หาเอง)")]
    public MQTTCore mqtt;

    [Header("Topic")]
    public string topicJoints = "dt/vision/person1/joints";

    [Header("2D Mapping")]
    public float worldWidth = 10f;   // x: 0..1 -> -5..+5 (เมื่อ worldWidth=10)
    public float worldHeight = 6f;   // y: 0..1 -> +3..-3 (invert)
    public float minVis = 0.6f;

    [Serializable] public class JointItem { public string name; public float x; public float y; public float v; }
    [Serializable] public class JointsMsg { public double ts; public string id; public JointItem[] joints; }

    // cache ล่าสุดของ joint (normalized)
    private readonly Dictionary<string, JointItem> cache = new Dictionary<string, JointItem>();

    void Start()
    {
        if (mqtt == null) mqtt = FindObjectOfType<MQTTCore>();
        if (mqtt == null)
        {
            Debug.LogError("JointStreamStore: ไม่พบ MQTTCore ใน Scene");
            return;
        }

        // รับ message ผ่าน event ของ MQTTCore ตัวจริง
        MQTTCore.OnMessageReceived += HandleMessage;
        MQTTCore.OnConnected += HandleConnected;

        // ลอง subscribe ทันที (ถ้ายังไม่ connected MQTTCore จะเตือนเอง)
        mqtt.Subscribe(topicJoints);
    }

    void HandleConnected()
    {
        // ตอน connect สำเร็จค่อย subscribe ซ้ำอีกรอบให้ชัวร์
        if (mqtt != null) mqtt.Subscribe(topicJoints);
    }

    void HandleMessage(string topic, string payload)
    {
        if (topic != topicJoints) return;

        var msg = JsonUtility.FromJson<JointsMsg>(payload);
        if (msg == null || msg.joints == null) return;

        foreach (var j in msg.joints)
        {
            if (j == null || string.IsNullOrEmpty(j.name)) continue;
            cache[j.name] = j;
        }
    }

    // ---- API ให้ PartFollower เรียก ----

    public bool TryGetJointWorld(string name, out Vector3 worldPos)
    {
        // virtual joints
        if (name == "hip_center")
            return TryGetMid("hip_l", "hip_r", out worldPos);
        if (name == "shoulder_center")
            return TryGetMid("shoulder_l", "shoulder_r", out worldPos);

        worldPos = default;

        if (!cache.ContainsKey(name)) return false;
        var j = cache[name];
        if (j.v < minVis) return false;

        worldPos = MapNormToWorld(j.x, j.y);
        return true;
    }

    bool TryGetMid(string a, string b, out Vector3 worldPos)
    {
        worldPos = default;
        if (!cache.ContainsKey(a) || !cache.ContainsKey(b)) return false;
        var ja = cache[a];
        var jb = cache[b];
        if (ja.v < minVis || jb.v < minVis) return false;

        float x = (ja.x + jb.x) / 2f;
        float y = (ja.y + jb.y) / 2f;
        worldPos = MapNormToWorld(x, y);
        return true;
    }

    Vector3 MapNormToWorld(float x, float y)
    {
        // image y ลงล่าง -> unity y ขึ้นบน: invert
        float wx = (x - 0.5f) * worldWidth;
        float wy = (0.5f - y) * worldHeight;
        return new Vector3(wx, wy, 0f);
    }

    void OnDestroy()
    {
        MQTTCore.OnMessageReceived -= HandleMessage;
        MQTTCore.OnConnected -= HandleConnected;
    }
}