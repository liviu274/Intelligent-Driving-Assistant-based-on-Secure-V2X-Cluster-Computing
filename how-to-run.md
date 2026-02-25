## Running with Virtual Environment and sudo

The V2X scripts require `sudo` for raw socket access. Use the full path to the venv's Python:

### Single Station (CAM Broadcast)
```bash
cd /home/liviu/v2x-messaging/Security-Analysis-and-Attack-Detection-Framework-for-ETSI-GeoNetworking-FlexStack-based-/app
sudo /home/liviu/v2x-messaging/.venv/bin/python cam_boradcast.py
```

### Multiple Stations (Cluster)
```bash
cd /home/liviu/v2x-messaging/Security-Analysis-and-Attack-Detection-Framework-for-ETSI-GeoNetworking-FlexStack-based-/app
sudo /home/liviu/v2x-messaging/.venv/bin/python cluster_launcher.py --stations 5
```

### Position Spoofing Attack Scenarios

#### Scenario 1: Static Position Spoofing
Attacker claims to be 10km away from real position:
```bash
cd /home/liviu/v2x-messaging/Security-Analysis-and-Attack-Detection-Framework-for-ETSI-GeoNetworking-FlexStack-based-/app
sudo /home/liviu/v2x-messaging/.venv/bin/python attack_orchestrator.py --legitimate 5 --attack-type static
```

#### Scenario 2: Teleportation Attack
Attacker alternates between two distant positions every 5 seconds:
```bash
sudo /home/liviu/v2x-messaging/.venv/bin/python attack_orchestrator.py --legitimate 5 --attack-type teleport
```

#### Scenario 3: Random Position Spoofing
Attacker broadcasts random positions within 20km every 2 seconds:
```bash
sudo /home/liviu/v2x-messaging/.venv/bin/python attack_orchestrator.py --legitimate 5 --attack-type random
```

#### Scenario 4: Manual Attacker (Single Station)
Run attacker standalone for custom testing:
```bash
sudo /home/liviu/v2x-messaging/.venv/bin/python cam_attacker.py --attack-type teleport
```

### Original GeoNetworking Example
```bash
cd /home/liviu/v2x-messaging/Security-Analysis-and-Attack-Detection-Framework-for-ETSI-GeoNetworking-FlexStack-based-
sudo /home/liviu/v2x-messaging/.venv/bin/python geonetworking_example.py
```

---

## Attack Detection Research

The attack scenarios simulate the threat model from your research notebook:
- **Cryptographically valid** CAMs (no broken signatures)
- **Semantically false** position data (insider attack)
- **Detection opportunity**: Plausibility checks on:
  - Sudden position jumps (teleportation)
  - Impossible speeds (>200 km/h for passenger cars)
  - Trajectory inconsistencies
  - Position vs. neighbor table history

### Viewing Attack Logs
Use the log-enabled launcher to track each station separately:
```bash
sudo /home/liviu/v2x-messaging/.venv/bin/python cluster_launcher_with_logs.py --stations 3
tail -f station_*.log  # Watch all logs in real-time
```