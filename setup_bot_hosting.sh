#!/bin/bash

# === CONFIGURATION ===
BOT_USER="abhishrent"
BOT_DIR="$(cd \"$(dirname \"$0\")\" && pwd)"
BOT_ENTRY="main.py"
SERVICE_NAME="discordbot"
PYTHON_EXEC=$(which python3)

# === DETECT PACKAGE MANAGER ===
if command -v apt &> /dev/null; then
    PM="apt"
    INSTALL_CMD="sudo apt update && sudo apt install -y python3"
elif command -v dnf &> /dev/null; then
    PM="dnf"
    INSTALL_CMD="sudo dnf install -y python3"
else
    echo "Unsupported package manager. Please install Python3 manually."
    exit 1
fi

echo "Using package manager: $PM"

# === INSTALL PYTHON3 IF NEEDED ===
if [ ! -x "$PYTHON_EXEC" ]; then
    echo "Python3 not found. Installing..."
    eval $INSTALL_CMD
else
    echo "Python3 found at $PYTHON_EXEC"
fi

# === CREATE SYSTEMD SERVICE FILE ===
SERVICE_PATH="/etc/systemd/system/${SERVICE_NAME}.service"

echo "Creating systemd service file at $SERVICE_PATH"

# === CREATE CONNECTIVITY CHECK SCRIPT ===
CONNECTIVITY_SCRIPT="/usr/local/bin/wait-for-connectivity.sh"
echo "Creating connectivity check script..."

sudo bash -c "cat > $CONNECTIVITY_SCRIPT" <<'EOF'
#!/bin/bash
MAX_ATTEMPTS=30
ATTEMPT=0
DELAY=10

echo "Waiting for internet connectivity..."

while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
    ATTEMPT=$((ATTEMPT + 1))
    echo "Attempt $ATTEMPT/$MAX_ATTEMPTS: Checking connectivity..."

    # Try multiple connectivity checks
    if ping -c 1 -W 5 8.8.8.8 &>/dev/null || \
       ping -c 1 -W 5 1.1.1.1 &>/dev/null || \
       curl -s --max-time 5 --connect-timeout 5 https://discord.com &>/dev/null; then
        echo "✓ Internet connectivity confirmed"
        exit 0
    fi

    echo "No connectivity yet, waiting ${DELAY}s..."
    sleep $DELAY
done

echo "⚠ Failed to establish internet connectivity after $MAX_ATTEMPTS attempts"
exit 1
EOF

sudo chmod +x $CONNECTIVITY_SCRIPT

sudo bash -c "cat > $SERVICE_PATH" <<EOF
[Unit]
Description=Discord Bot
After=network-online.target
Wants=network-online.target
StartLimitIntervalSec=300
StartLimitBurst=5

[Service]
Type=simple
ExecStartPre=$CONNECTIVITY_SCRIPT
ExecStart=$PYTHON_EXEC $BOT_DIR/$BOT_ENTRY
WorkingDirectory=$BOT_DIR
Restart=on-failure
RestartSec=30
User=$BOT_USER
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF

# === SET DIRECTORY PERMISSIONS ===
echo "Setting permissions for bot directory..."
sudo chown -R $BOT_USER:$BOT_USER $BOT_DIR
sudo chmod -R 755 $BOT_DIR

# === ENABLE AND START THE SERVICE ===
echo "Reloading systemd..."
sudo systemctl daemon-reload

echo "Enabling the bot service..."
sudo systemctl enable $SERVICE_NAME

# === TEST NETWORK CONNECTIVITY FIRST ===
echo "Testing network connectivity..."
if ping -c 1 discord.com &> /dev/null; then
    echo "✓ Network connectivity to Discord confirmed"
    echo "Starting the bot service..."
    sudo systemctl start $SERVICE_NAME
else
    echo "⚠ WARNING: Cannot reach discord.com"
    echo "Please check your network connection and DNS settings"
    echo "You can start the service manually later with:"
    echo "  sudo systemctl start $SERVICE_NAME"
fi

# === CHECK STATUS ===
echo "Checking service status..."
sudo systemctl status $SERVICE_NAME --no-pager

# === SHOW LOG TAIL COMMAND ===
echo
echo "To check logs later, run:"
echo "  journalctl -u $SERVICE_NAME --no-pager --lines=50"
echo "To restart the service:"
echo "  sudo systemctl restart $SERVICE_NAME"
