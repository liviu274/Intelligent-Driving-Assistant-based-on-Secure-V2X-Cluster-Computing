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
