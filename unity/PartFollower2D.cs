using UnityEngine;

public class PartFollower2D : MonoBehaviour
{
    public JointStreamStore store;

    [Header("Mode")]
    public bool useBone = true;

    [Header("Bone Mode")]
    public string jointA = "shoulder_l";
    public string jointB = "wrist_l";

    [Header("Point Mode (ถ้า useBone=false)")]
    public string jointPoint = "head";

    [Header("Tuning")]
    public float thickness = 0.2f;           // ความหนาแท่ง
    public float rotationOffsetDeg = 0f;     // ชดเชยมุมเริ่มต้นของ sprite/model
    public bool flipDirection = false;       // สลับ A/B

    void Reset()
    {
        thickness = 0.2f;
        rotationOffsetDeg = 0f;
        useBone = true;
    }

    void Update()
    {
        if (store == null) return;

        if (!useBone)
        {
            if (store.TryGetJointWorld(jointPoint, out var p))
                transform.position = p;
            return;
        }

        string a = flipDirection ? jointB : jointA;
        string b = flipDirection ? jointA : jointB;

        if (!store.TryGetJointWorld(a, out var p1)) return;
        if (!store.TryGetJointWorld(b, out var p2)) return;

        Vector3 d = (p2 - p1);
        float len = d.magnitude;
        if (len < 1e-5f) return;

        Vector3 mid = (p1 + p2) * 0.5f;
        float angle = Mathf.Atan2(d.y, d.x) * Mathf.Rad2Deg + rotationOffsetDeg;

        transform.position = mid;
        transform.rotation = Quaternion.Euler(0, 0, angle);

        // object ต้องยาวตามแกน X
        transform.localScale = new Vector3(len, thickness, 1f);
    }
}