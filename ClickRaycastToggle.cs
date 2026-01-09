using UnityEngine;
using UnityEngine.InputSystem;

public class ClickRaycastToggle : MonoBehaviour
{
    public Camera cam;
    public MQTTCore mqtt;
    public string commandTopic = "dgt/light/cmd";

    void Update()
    {
        if (Mouse.current == null) return;

        if (Mouse.current.leftButton.wasPressedThisFrame)
        {
            Ray ray = cam.ScreenPointToRay(Mouse.current.position.ReadValue());
            if (Physics.Raycast(ray, out RaycastHit hit))
            {
                if (hit.collider.CompareTag("Lamp"))
                {
                    Debug.Log("🖱 Lamp clicked (Input System)");
                    mqtt.Publish(commandTopic, "toggle");
                }
            }
        }
    }
}
