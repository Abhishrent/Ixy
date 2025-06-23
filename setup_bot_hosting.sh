#!/bin/bash

# === CONFIGURATION ===
BOT_USER="abhishrent"
# Get the absolute path of the directory containing this script
BOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BOT_ENTRY="main.py"
SERVICE_NAME="discordbot"
PYTHON_EXEC=$(which python3)

echo "Script location: $BOT_DIR"
echo "Bot entry point: $BOT_DIR/$BOT_ENTRY"

# === VERIFY BOT FILES EXIST ===
if [ ! -f "$BOT_DIR/$BOT_ENTRY" ]; then
    echo "ERROR: Bot entry point not found at $BOT_DIR/$BOT_ENTRY"
    echo "Please ensure this script is in the same directory as your bot files."
    exit 1
fi

# === DETECT PACKAGE MANAGER ===
if command -v apt &> /dev/null; then
    PM="apt"
    INSTALL_CMD="sudo apt update && sudo apt install -y python3 python3-pip"
elif command -v dnf &> /dev/null; then
    PM="dnf"
    INSTALL_CMD="sudo dnf install -y python3 python3-pip"
elif command -v pacman &> /dev/null; then
    PM="pacman"
    INSTALL_CMD="sudo pacman -S python python-pip"
else
    echo "Unsupported package manager. Please install Python3 manually."
    exit 1
fi

echo "Using package manager: $PM"

# === INSTALL PYTHON3 IF NEEDED ===
if [ ! -x "$PYTHON_EXEC" ]; then
    echo "Python3 not found. Installing..."
    eval $INSTALL_CMD
    PYTHON_EXEC=$(which python3)
else
    echo "Python3 found at $PYTHON_EXEC"
fi

# === VERIFY PYTHON EXECUTABLE ===
if [ ! -x "$PYTHON_EXEC" ]; then
    echo "ERROR: Python3 installation failed or not found in PATH"
    exit 1
fi

echo "Using Python: $PYTHON_EXEC"

# === CREATE SYSTEMD SERVICE FILE ===
SERVICE_PATH="/etc/systemd/system/${SERVICE_NAME}.service"

echo "Creating systemd service file at $SERVICE_PATH"

# === CREATE CONNECTIVITY CHECK SCRIPT ===
CONNECTIVITY_SCRIPT="/usr/local/bin/wait-for-connectivity.sh"
echo "Creating connectivity check script..."

sudo bash -c "cat > '$CONNECTIVITY_SCRIPT'" <<'EOF'
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

sudo chmod +x "$CONNECTIVITY_SCRIPT"

# === CREATE SERVICE FILE WITH PROPER PATHS ===
echo "Creating service file with paths:"
echo "  ExecStart: $PYTHON_EXEC $BOT_DIR/$BOT_ENTRY"
echo "  WorkingDirectory: $BOT_DIR"

sudo bash -c "cat > '$SERVICE_PATH'" <<EOF
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
Group=$BOT_USER
Environment=PYTHONUNBUFFERED=1
Environment=PATH=/usr/local/bin:/usr/bin:/bin

[Install]
WantedBy=multi-user.target
EOF

# === VERIFY SERVICE FILE WAS CREATED CORRECTLY ===
echo "Verifying service file contents:"
echo "----------------------------------------"
cat "$SERVICE_PATH"
echo "----------------------------------------"

# === SET DIRECTORY PERMISSIONS ===
echo "Setting permissions for bot directory..."
sudo chown -R "$BOT_USER:$BOT_USER" "$BOT_DIR"
sudo chmod -R 755 "$BOT_DIR"

# === INSTALL PYTHON DEPENDENCIES IF requirements.txt EXISTS ===
if [ -f "$BOT_DIR/requirements.txt" ]; then
    echo "Found requirements.txt, installing dependencies..."
    if command -v pip3 &> /dev/null; then
        sudo -u "$BOT_USER" pip3 install --user -r "$BOT_DIR/requirements.txt"
    else
        echo "pip3 not found, please install dependencies manually"
    fi
fi

# === STOP EXISTING SERVICE IF RUNNING ===
if systemctl is-active --quiet "$SERVICE_NAME"; then
    echo "Stopping existing $SERVICE_NAME service..."
    sudo systemctl stop "$SERVICE_NAME"
fi

# === ENABLE AND START THE SERVICE ===
echo "Reloading systemd..."
sudo systemctl daemon-reload

echo "Enabling the bot service..."
sudo systemctl enable "$SERVICE_NAME"

# === TEST NETWORK CONNECTIVITY FIRST ===
echo "Testing network connectivity..."
if ping -c 1 discord.com &> /dev/null; then
    echo "✓ Network connectivity to Discord confirmed"
    echo "Starting the bot service..."
    sudo systemctl start "$SERVICE_NAME"

    # Give it a moment to start
    sleep 3

    # Check if it's running
    if systemctl is-active --quiet "$SERVICE_NAME"; then
        echo "✓ Service started successfully"
    else
        echo "⚠ Service failed to start, checking logs..."
        journalctl -u "$SERVICE_NAME" --no-pager --lines=10
    fi
else
    echo "⚠ WARNING: Cannot reach discord.com"
    echo "Please check your network connection and DNS settings"
    echo "You can start the service manually later with:"
    echo "  sudo systemctl start $SERVICE_NAME"
fi

# === CHECK STATUS ===
echo "Checking service status..."
sudo systemctl status "$SERVICE_NAME" --no-pager --lines=10

# === SHOW USEFUL COMMANDS ===
echo
echo "=== USEFUL COMMANDS ==="
echo "Check logs (real-time):     journalctl -u $SERVICE_NAME -f"
echo "Check logs (last 50):       journalctl -u $SERVICE_NAME --no-pager --lines=50"
echo "Restart service:            sudo systemctl restart $SERVICE_NAME"
echo "Stop service:               sudo systemctl stop $SERVICE_NAME"
echo "Start service:              sudo systemctl start $SERVICE_NAME"
echo "Disable auto-start:         sudo systemctl disable $SERVICE_NAME"
echo "Check service status:       sudo systemctl status $SERVICE_NAME"
echo
echo "Bot directory: $BOT_DIR"
echo "Service file: $SERVICE_PATH"
