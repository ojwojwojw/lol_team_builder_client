#!/usr/bin/env bash
set -euo pipefail

APP_DIR=/opt/team_builder
PYTHON_BIN=python3

sudo apt-get update
sudo apt-get install -y python3-venv nginx

sudo mkdir -p "$APP_DIR"
sudo chown -R "$USER":"$USER" "$APP_DIR"

cd "$APP_DIR"

if [ ! -d .venv ]; then
  "$PYTHON_BIN" -m venv .venv
fi

. .venv/bin/activate
pip install --upgrade pip
pip install -r server/requirements.txt

mkdir -p data

echo "Bootstrap complete. Copy deploy/ec2/team-builder-api.service to /etc/systemd/system/ before starting the service."
