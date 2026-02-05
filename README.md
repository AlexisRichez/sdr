# Automatically Start scan_pmr.py on Raspberry Pi

This guide explains how to automatically start `scan_pmr.py` at Raspberry Pi boot using a Python virtual environment and systemd.

---

## Prerequisites

- Raspberry Pi running Linux
- Python installed
- A working Python virtual environment (example: `sdr-env`)
- `scan_pmr.py` script working when launched manually
- Script and environment located in `/home/pi` (adjust paths if needed)

---

## Step 1 — Create a systemd Service

Create a new service file:

```
sudo nano /etc/systemd/system/scanpmr.service
```
```
[Unit]
Description=Scan PMR Service
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi
ExecStart=/bin/bash -c "source /home/pi/sdr-env/bin/activate && python3 /home/pi/scan_pmr.py"
Restart=always
RestartSec=5
StandardOutput=append:/home/pi/scan.log
StandardError=append:/home/pi/scan.log

[Install]
WantedBy=multi-user.target
```

```
sudo systemctl daemon-reload
sudo systemctl enable scanpmr.service
sudo systemctl start scanpmr.service
tail -f /home/pi/scan.log
journalctl -u scanpmr.service -f
```
