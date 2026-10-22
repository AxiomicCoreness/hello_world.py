apiVersion: apps/v1
kind: Deployment
metadata:
  name: clarke-yoursa-tee-worker
  namespace: seagate-mimic
  labels:
    app: sovereign-worker
spec:
  replicas: 0 # Default to 0 for safety (matches script output)
  selector:
    matchLabels:
      app: sovereign-worker
  template:
    metadata:
      labels:
        app: sovereign-worker
    spec:
      containers:
      - name: deepinfer-worker
        image: registry.local/sovereign/deepinfer:nvidia-2.32.3
        command: ["python", "-m", "deepinfer.entrypoints.launch_worker"]
        env:
        - name: CUDA_VISIBLE_DEVICES
          value: "0" # Maps to self.local_rank
        - name: DEEPINFER_GC_INTERVAL_STEP
          value: "100"
        resources:
          limits:
            nvidia.com/gpu: 1
            cpu: "8"
            memory: "32Gi"
          requests:
            nvidia.com/gpu: 1
            cpu: "4"
            memory: "16Gi"
      # Needed for distributed NCCL communication over TCP
      hostNetwork: true
      dnsPolicy: ClusterFirstWithHostNet
