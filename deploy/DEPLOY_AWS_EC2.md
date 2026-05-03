# AWS EC2 Deployment Guide

This project currently fits best on one small EC2 instance because the backend is a single FastAPI app with a local SQLite database.

## Recommended first deployment

- EC2: `t3.small` or `t3.micro`
- OS: Ubuntu 24.04 LTS
- Storage: 20 GB is enough to start
- Open ports in the security group:
  - `22` for SSH from your IP only
  - `80` for HTTP
  - `443` for HTTPS

## 1. Create the instance

1. In AWS, create an EC2 instance with Ubuntu.
2. Download the `.pem` key.
3. Connect from your local machine:

```bash
ssh -i /path/to/key.pem ubuntu@YOUR_EC2_PUBLIC_IP
```

## 2. Copy the project to the server

If you use git:

```bash
sudo mkdir -p /opt
sudo chown ubuntu:ubuntu /opt
cd /opt
git clone <your-repo-url> team_builder
cd /opt/team_builder
```

If you are not using git yet, you can upload the project folder with `scp` or a Git client first.

## 3. Install runtime packages

```bash
cd /opt/team_builder
chmod +x deploy/ec2/bootstrap_server.sh
./deploy/ec2/bootstrap_server.sh
```

## 4. Set production secrets

Create `server/.env` on the EC2 instance:

```bash
cat <<'EOF' > /opt/team_builder/server/.env
TEAM_BUILDER_JWT_SECRET=replace-with-a-long-random-secret
TEAM_BUILDER_CORS_ORIGINS=
EOF
```

Notes:

- `TEAM_BUILDER_JWT_SECRET` should be a long random string.
- `TEAM_BUILDER_CORS_ORIGINS` can stay empty for the current desktop client.
- The SQLite DB will be created automatically at `/opt/team_builder/data/riot_matches.db`.

## 5. Register the systemd service

```bash
sudo cp /opt/team_builder/deploy/ec2/team-builder-api.service /etc/systemd/system/team-builder-api.service
sudo systemctl daemon-reload
sudo systemctl enable team-builder-api
sudo systemctl start team-builder-api
sudo systemctl status team-builder-api
```

Health check:

```bash
curl http://127.0.0.1:8000/health
```

## 6. Put Nginx in front

```bash
sudo cp /opt/team_builder/deploy/ec2/nginx-team-builder.conf /etc/nginx/sites-available/team-builder
sudo ln -s /etc/nginx/sites-available/team-builder /etc/nginx/sites-enabled/team-builder
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx
```

Now test:

```bash
curl http://YOUR_EC2_PUBLIC_IP/health
```

## 7. Add HTTPS

Install Certbot after you connect a domain to the EC2 public IP:

```bash
sudo apt-get install -y certbot python3-certbot-nginx
sudo certbot --nginx -d api.your-domain.com
```

For production, HTTPS is strongly recommended because login tokens and Riot API requests should not go over plain HTTP.

## 8. Connect the desktop client

Change the client server address from:

```text
http://127.0.0.1:8000
```

to:

```text
https://api.your-domain.com
```

If you do not have a domain yet, you can temporarily use:

```text
http://YOUR_EC2_PUBLIC_IP
```

## Operations

Restart service:

```bash
sudo systemctl restart team-builder-api
```

View logs:

```bash
sudo journalctl -u team-builder-api -f
```

## Important limitation

This deployment uses SQLite on one server. That is fine for a small internal tool, but if you later want multiple app servers or stronger durability, move the DB to PostgreSQL or RDS.
