using System;
using System.Collections.Generic;
using UnityEngine;

public class UnityMainThreadDispatcher : MonoBehaviour
{
    private static readonly Queue<Action> jobQueue = new Queue<Action>();
    public static UnityMainThreadDispatcher Instance;

    void Awake()
    {
        if (Instance == null)
        {
            Instance = this;
            DontDestroyOnLoad(this.gameObject);
        }
        else
        {
            Destroy(gameObject);
        }
    }

    void Update()
    {
        lock (jobQueue)
        {
            while (jobQueue.Count > 0)
            {
                jobQueue.Dequeue()?.Invoke();
            }
        }
    }

    public void Enqueue(Action job)
    {
        if (job == null) return;
        lock (jobQueue)
        {
            jobQueue.Enqueue(job);
        }
    }
}
