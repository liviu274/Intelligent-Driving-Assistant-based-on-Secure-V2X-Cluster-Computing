Run it with the venv’s Python directly (no activation needed):

```bash
cd /home/liviu/v2x-messaging
sudo -E /home/liviu/.venv/bin/python geonetworking_example.py
```

If `sudo -E` still drops the venv, use:

```bash
sudo env PATH="/home/liviu/.venv/bin:$PATH" /home/liviu/.venv/bin/python geonetworking_example.py
```