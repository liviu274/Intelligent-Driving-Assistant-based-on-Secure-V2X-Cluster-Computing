# Security-Analysis-and-Attack-Detection-Framework-for-ETSI-GeoNetworking-FlexStack-based-
Design and implement a security monitoring and attack-detection module for the GeoNetworking layer using FlexStack, focusing on realistic attacks against V2X communication such as position spoofing, replay attacks, and flooding, and demonstrate detection + mitigation strategies.

## Live Map GUI

Run the local map server:

```bash
python app/web_gui/server.py --port 8000
```

Launch the station cluster and point it at the telemetry endpoint:

```bash
cd app
sudo /home/liviu/v2x-messaging/.venv/bin/python cluster_launcher.py --stations 5 --location dtr --telemetry-url http://127.0.0.1:8000/api/telemetry
```

Then open `http://127.0.0.1:8000` to see every live station on the map.

## Attack Collection Script

A helper wrapper is available at `results/run_collect_cluster_attacks.sh`.
Run it from the repository root to clean `app/data/cam_trace.csv`, start the cluster, schedule attacks, and capture data for 120 seconds:

```bash
./results/run_collect_cluster_attacks.sh
```

Additional options may be passed through to `collect_cluster_attacks.py` as needed.
