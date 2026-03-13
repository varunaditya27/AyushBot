# =============================================================================
# AyushBot Infrastructure — Raspberry Pi 4 Gateway Setup Script
# =============================================================================
#
# PURPOSE:
#   One-time setup script for provisioning a fresh Raspberry Pi 4 as an
#   AyushBot PHC gateway. Run this on a new RPi 4 running Raspberry Pi OS
#   (64-bit Bullseye or Bookworm) to install all dependencies and configure
#   the system for unattended operation.
#
# WHAT THIS SCRIPT DOES:
#
#   1. System Update & Essential Packages
#      - apt update && upgrade
#      - Install: git, curl, python3, python3-pip, python3-venv
#      - Install: docker, docker-compose (for containerized deployment)
#      - Install: bluez (Bluetooth stack for BLE communication)
#
#   2. Docker Installation
#      - Install Docker CE for ARM64
#      - Add the 'pi' user to the docker group
#      - Enable Docker to start at boot (systemctl enable docker)
#
#   3. Python Environment
#      - Create a Python 3.11+ virtual environment at /opt/ayushbot/venv
#      - Install backend/requirements.txt into the venv
#      - Pin all dependency versions for reproducibility
#
#   4. TLS Certificate Setup
#      - Generate self-signed CA + server + client certificates for:
#        a. MQTT broker (Mosquitto) TLS
#        b. Backend HTTPS (if exposed)
#        c. Flower FL client mTLS
#      - Store in /opt/ayushbot/certs/ with restrictive permissions (600)
#      - In production, replace self-signed with proper PKI certificates
#
#   5. Bluetooth Configuration
#      - Enable BLE adapter (hciconfig hci0 up)
#      - Configure BlueZ for passive scanning (battery efficient)
#      - Set up BLE GATT client systemd service for auto-connecting
#        to the Arduino sensor pack
#
#   6. Storage Setup
#      - Create data directories: /opt/ayushbot/data/, /opt/ayushbot/models/
#      - Mount external USB storage if available (for larger model files)
#      - Configure log rotation (prevent SD card filling up)
#
#   7. Systemd Services
#      - Create systemd unit files for:
#        a. ayushbot-gateway.service (Docker Compose up)
#        b. ayushbot-ble.service (BLE sensor bridge)
#      - Enable services to start at boot
#      - Configure watchdog (restart if service dies)
#
#   8. Network Configuration
#      - Configure WiFi (if available) for internet connectivity
#      - Set up a local hotspot mode as fallback (for Android phone connection)
#      - Configure firewall (ufw): allow only MQTT, HTTP, and BLE
#
#   9. Swap & Performance Tuning
#      - Increase swap to 2 GB (for LLM inference memory headroom)
#      - Set GPU memory to minimum (16 MB — headless operation)
#      - Disable unnecessary services (GUI, avahi, triggerhappy)
#
# USAGE:
#   chmod +x infra/rpi_setup.sh
#   sudo ./infra/rpi_setup.sh
#
# PREREQUISITES:
#   - Raspberry Pi 4 (4 GB RAM recommended, 8 GB ideal)
#   - Raspberry Pi OS 64-bit (Bullseye or Bookworm)
#   - Internet connection (for package downloads)
#   - SSH access configured
# =============================================================================
