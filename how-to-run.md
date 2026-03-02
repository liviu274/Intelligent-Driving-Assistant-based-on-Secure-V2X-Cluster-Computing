## Running with Virtual Environment and sudo

The V2X scripts require `sudo` for raw socket access. Use the full path to the venv's Python:

### Single Station (CAM Broadcast)
```bash
cd app
sudo /home/liviu/v2x-messaging/.venv/bin/python cam_boradcast.py
```

### Multiple Stations (Cluster)
```bash
cd app
sudo /home/liviu/v2x-messaging/.venv/bin/python cluster_launcher.py --stations 5
```

### Position Spoofing Attack Scenarios

#### Scenario 1: Static Position Spoofing
Attacker claims to be 10km away from real position:
 -- uing a 2 terminal configuration --

terminal 1:

```bash
cd app
sudo /home/liviu/v2x-messaging/.venv/bin/python cluster_launcher.py --stations 5
```

terminal 2:
```bash
cd attacker
sudo /home/liviu/v2x-messaging/.venv/bin/python attack_orchestrator.py --count 1 --attack-type 1
```


## Attack Detection Research

The attack scenarios simulate the threat model from your research notebook:
- **Cryptographically valid** CAMs (no broken signatures)
- **Semantically false** position data (insider attack)
- **Detection opportunity**: Plausibility checks on:
  - Sudden position jumps (teleportation)
  - Impossible speeds (>300 km/h for passenger cars)
  - Trajectory inconsistencies
  - Position vs. neighbor table history

### Viewing Attack Logs
Use the log-enabled launcher to track each station separately:
```bash
sudo /home/liviu/v2x-messaging/.venv/bin/python cluster_launcher_with_logs.py --stations 3
tail -f station_*.log  # Watch all logs in real-time
```