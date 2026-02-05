# RTL-SDR project

## Install SDR environment
```
sudo apt update
sudo apt install rtl-sdr
sudo apt install python3-pip
sudo apt install python3-full python3-venv
python3 -m venv sdr-env
source sdr-env/bin/activate
pip install numpy pyrtlsdr
pip install --upgrade pip setuptools wheel
pip install scipy
pip install numpy
```

```
sudo nano /etc/udev/rules.d/20-rtl-sdr.rules
# RTL-SDR USB devices
SUBSYSTEM=="usb", ATTR{idVendor}=="0bda", ATTR{idProduct}=="2838", MODE="0666"
SUBSYSTEM=="usb", ATTR{idVendor}=="0bda", ATTR{idProduct}=="2832", MODE="0666"
SUBSYSTEM=="usb", ATTR{idVendor}=="0bda", ATTR{idProduct}=="2830", MODE="0666"
sudo udevadm control --reload-rules
sudo udevadm trigger
```

```
sudo cp /usr/share/rtl-sdr/rtl-sdr.rules /etc/udev/rules.d/
sudo udevadm control --reload-rules
sudo udevadm trigger
```

## Automatically Start scan_pmr.py

### Prerequisites

- Raspberry Pi running Linux
- Python installed
- A working Python virtual environment (example: `sdr-env`)
- `scan_pmr.py` script working when launched manually
- Script and environment located in `/home/pi` (adjust paths if needed)

---

### Create a systemd Service

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
