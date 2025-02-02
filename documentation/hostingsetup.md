# Systemd Discord Bot Service Cheatsheet

## Setup Process

### 1. Create service file
```bash
sudo nano /etc/systemd/system/discordbot.service
```

### 2. Add this content to the service file
```ini
[Unit]
Description=Discord Bot
After=network-online.target
Wants=network-online.target

[Service]
ExecStart=/usr/bin/python3 /home/abhishrent/Projects/Python/discordbot/main.py
WorkingDirectory=/home/abhishrent/Projects/Python/discordbot
Restart=always
User=abhishrent

[Install]
WantedBy=multi-user.target
```

### 3. Enable and start service
```bash
sudo systemctl enable discordbot.service
sudo systemctl start discordbot.service
```

## Monitoring Commands

### Check status
```bash
systemctl status discordbot.service
```

### View logs
```bash
# View last 50 lines
journalctl -u discordbot.service -n 50

# Follow logs in real-time (Ctrl+C to exit)
journalctl -u discordbot.service -f

# View logs since last boot
journalctl -u discordbot.service -b
```

### Manage service
```bash
# Reload after making changes
sudo systemctl daemon-reload
sudo systemctl restart discordbot.service

# Stop service
sudo systemctl stop discordbot.service
```

## Cleanup/Uninstall

```bash
# Stop and disable the service
sudo systemctl stop discordbot.service
sudo systemctl disable discordbot.service

# Remove service file
sudo rm /etc/systemd/system/discordbot.service

# Reload systemd to recognize changes
sudo systemctl daemon-reload

# Reset failed units
sudo systemctl reset-failed
```