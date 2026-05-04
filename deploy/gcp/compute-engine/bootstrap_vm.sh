#!/usr/bin/env bash
set -euo pipefail

APP_DIR=/opt/team_builder

sudo apt-get update
sudo apt-get install -y docker.io nginx

sudo systemctl enable docker
sudo systemctl start docker

sudo mkdir -p "$APP_DIR/secrets"
sudo chown -R "$USER":"$USER" "$APP_DIR"

if [ ! -f "$APP_DIR/server.env" ]; then
  cat > "$APP_DIR/server.env" <<'EOF'
TEAM_BUILDER_JWT_SECRET=replace-with-a-long-random-secret
TEAM_BUILDER_CORS_ORIGINS=
TEAM_BUILDER_RIOT_API_KEY=
TEAM_BUILDER_FIRESTORE_PROJECT=
TEAM_BUILDER_FIRESTORE_DATABASE=(default)
GOOGLE_APPLICATION_CREDENTIALS=/app/secrets/service-account.json
EOF
  echo "Created $APP_DIR/server.env. Edit it before starting the service."
fi

echo "Bootstrap complete."
echo "Next steps:"
echo "1. Copy the project into $APP_DIR"
echo "2. Put your Firestore service account JSON at $APP_DIR/secrets/service-account.json"
echo "3. Build the image: sudo docker build -t team-builder-api $APP_DIR"
echo "4. Copy deploy/gcp/compute-engine/team-builder-api.service to /etc/systemd/system/"
echo "5. Start the systemd service"
