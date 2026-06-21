# 🚀 AyushBot Cloud Deployment Guide

**Document Version**: 1.0  
**Last Updated**: May 31, 2026  
**Target Audience**: DevOps Engineers, Cloud Architects, System Administrators

---

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Local Development Setup](#local-development-setup)
4. [Production Deployment](#production-deployment)
5. [Configuration & Secrets Management](#configuration--secrets-management)
6. [Monitoring & Troubleshooting](#monitoring--troubleshooting)
7. [Backup & Disaster Recovery](#backup--disaster-recovery)
8. [Scaling & Performance](#scaling--performance)
9. [Security Best Practices](#security-best-practices)
10. [Rollback Procedures](#rollback-procedures)

---

## Overview

AyushBot Cloud is a multi-container microservices architecture consisting of:

| Service | Port | Purpose | Container |
|---------|------|---------|-----------|
| **FL Server** | 8080 | Federated Learning orchestration (gRPC) | flower:2.x |
| **Cloud API** | 8443 | REST API with TLS/mTLS (HTTPS) | FastAPI |
| **Analytics Dashboard** | 8501 | Real-time monitoring (Streamlit) | Streamlit |
| **PostgreSQL** | 5432 | Audit logs, state management | postgres:16-alpine |
| **InfluxDB** | 8086 | Time-series metrics | influxdb:2.7-alpine |

**Architecture Diagram**:
```
┌─────────────────────────────────────────────────────────────┐
│                    Docker Compose Network                    │
│                   (ayushbot-cloud-net)                       │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  FL Server   │  │ Cloud API    │  │  Analytics   │      │
│  │  :8080       │  │  :8443 TLS   │  │  :8501       │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
│         │                  │                  │               │
│         └──────────────────┼──────────────────┘               │
│                            │                                  │
│              ┌─────────────┴─────────────┐                   │
│              │                           │                   │
│         ┌────▼─────┐            ┌───────▼────┐              │
│         │PostgreSQL│            │  InfluxDB  │              │
│         │:5432     │            │  :8086     │              │
│         └──────────┘            └────────────┘              │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## Prerequisites

### System Requirements

**Minimum (Development)**:
- CPU: 2 cores
- RAM: 4 GB
- Disk: 20 GB SSD
- OS: Linux (Ubuntu 20.04+), macOS, or Windows (WSL2)

**Recommended (Production)**:
- CPU: 8 cores
- RAM: 16 GB
- Disk: 100 GB SSD (RAID-1 for HA)
- OS: Ubuntu 22.04 LTS or CentOS 8+
- Network: 100 Mbps+ bandwidth

### Required Software

```bash
# Docker (20.10+)
docker --version
# Docker Compose (2.0+)
docker compose version

# Verify installation
docker run hello-world
docker compose --version
```

**Installation**:
```bash
# Ubuntu/Debian
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# macOS (using Homebrew)
brew install docker docker-compose

# Windows (using Docker Desktop)
# Download from https://www.docker.com/products/docker-desktop
```

### Git & Repository Access

```bash
git clone https://github.com/varunaditya27/AyushBot.git
cd AyushBot/AyushBot/cloud
```

---

## Local Development Setup

### Step 1: Clone & Setup

```bash
# Clone repository
git clone https://github.com/varunaditya27/AyushBot.git
cd AyushBot/AyushBot/cloud

# Copy environment template
cp .env.example .env.dev

# Generate TLS certificates for local testing (optional)
python generate_certs.py --output-dir ./certs --force
```

### Step 2: Start Services

```bash
# Start all services in development mode
docker compose up --build

# OR run in background
docker compose up -d --build

# View logs
docker compose logs -f

# View specific service logs
docker compose logs -f cloud-api
docker compose logs -f cloud-fl-server
```

### Step 3: Verify Services

```bash
# Check service status
docker compose ps

# Test endpoints
curl http://localhost:8080/health           # FL Server
curl -k https://localhost:8443/api/v1/health/  # Cloud API (TLS)
curl http://localhost:8501                  # Analytics Dashboard
curl http://localhost:5432                  # PostgreSQL (psql)
curl http://localhost:8086/ping             # InfluxDB
```

### Step 4: Access Services

| Service | URL | Credentials |
|---------|-----|-------------|
| **Analytics Dashboard** | http://localhost:8501 | None (public in dev) |
| **Flower UI** (if available) | http://localhost:8080 | None |
| **InfluxDB UI** | http://localhost:8086 | admin / admin_dev_password |
| **PostgreSQL** | psql -h localhost -U ayushbot | Password: dev_password_change_me |

### Step 5: Stop Services

```bash
# Stop all services (keep data)
docker compose stop

# Stop and remove containers (keep volumes)
docker compose down

# Stop and remove everything (including volumes)
docker compose down -v
```

---

## Production Deployment

### Step 1: Prepare Infrastructure

#### Option A: Cloud VM (AWS EC2, GCP Compute, Azure VM)

```bash
# 1. Launch VM
# - Image: Ubuntu 22.04 LTS
# - Instance Type: t3.xlarge (4 vCPU, 16 GB RAM)
# - Storage: 100 GB gp3 SSD
# - Security Group: Allow ports 8080, 8443, 8501, 22 (SSH)

# 2. SSH into VM
ssh -i key.pem ubuntu@PUBLIC_IP

# 3. Update system
sudo apt-get update && sudo apt-get upgrade -y

# 4. Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker ubuntu
```

#### Option B: Kubernetes (EKS, GKE, AKS)

```yaml
# Create a simple Kubernetes deployment (example)
# See cloud/k8s/ directory for full manifests
apiVersion: v1
kind: Pod
metadata:
  name: ayushbot-cloud
spec:
  containers:
  - name: cloud-api
    image: ayushbot-cloud:latest
    ports:
    - containerPort: 8443
```

### Step 2: Create Production Environment

```bash
# Copy environment template
cp .env.example .env.prod

# Edit .env.prod with production values
# ⚠️ CRITICAL: Set strong passwords!
nano .env.prod

# Example production settings:
# POSTGRES_PASSWORD=generated_random_32_chars
# INFLUXDB_ADMIN_PASSWORD=generated_random_32_chars
# API_SECRET_KEY=generated_random_64_chars
# ENABLE_TLS=true
# ENVIRONMENT=production
```

### Step 3: Generate TLS Certificates

```bash
# For self-signed (testing)
python generate_certs.py --output-dir ./certs --force

# For Let's Encrypt (production recommended)
# Using Certbot with DNS validation
sudo apt-get install certbot python3-certbot-dns-route53
certbot certonly --dns-route53 -d cloud.ayushbot.io

# Copy certificates to certs/ directory
cp /etc/letsencrypt/live/cloud.ayushbot.io/fullchain.pem ./certs/server.crt
cp /etc/letsencrypt/live/cloud.ayushbot.io/privkey.pem ./certs/server.key
```

### Step 4: Build & Push Docker Images

```bash
# Build images locally
docker compose build

# Tag images for registry
docker tag ayushbot-cloud-cloud-fl-server:latest gcr.io/your-project/ayushbot-fl-server:1.0.0
docker tag ayushbot-cloud-cloud-api:latest gcr.io/your-project/ayushbot-api:1.0.0
docker tag ayushbot-cloud-cloud-analytics:latest gcr.io/your-project/ayushbot-analytics:1.0.0

# Push to container registry
docker push gcr.io/your-project/ayushbot-fl-server:1.0.0
docker push gcr.io/your-project/ayushbot-api:1.0.0
docker push gcr.io/your-project/ayushbot-analytics:1.0.0
```

### Step 5: Deploy to Production

```bash
# Method 1: Direct Docker Compose (small deployment)
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Method 2: Kubernetes (scalable deployment)
kubectl apply -f cloud/k8s/

# Method 3: Cloud Deployment (GCP Cloud Run, AWS ECS, etc.)
# See cloud-specific deployment guides
```

### Step 6: Verify Production Deployment

```bash
# Check all services running
docker compose ps

# Verify service health
curl https://cloud.ayushbot.io:8443/api/v1/health/
curl https://cloud.ayushbot.io:8080/health

# Check logs
docker compose logs --tail=100

# Monitor resource usage
docker stats
```

---

## Configuration & Secrets Management

### Environment Variables

All configuration is managed via environment variables in `.env.prod`:

```bash
# PostgreSQL
POSTGRES_USER=ayushbot
POSTGRES_PASSWORD=secure_password_here

# InfluxDB
INFLUXDB_ADMIN_USER=admin
INFLUXDB_ADMIN_PASSWORD=secure_password_here

# TLS/mTLS
ENABLE_TLS=true
CERTFILE=/app/certs/server.crt
KEYFILE=/app/certs/server.key

# Federated Learning
FL_MIN_CLIENTS=5
FL_STRATEGY=FedProx
FL_ROUNDS=20

# Logging
LOG_LEVEL=WARNING
```

### Secrets Management Best Practices

```bash
# ✅ DO: Use external secrets manager
# AWS Secrets Manager
aws secretsmanager get-secret-value --secret-id ayushbot-prod

# Google Secret Manager
gcloud secrets versions access latest --secret="ayushbot-prod"

# HashiCorp Vault
vault kv get secret/ayushbot/prod

# ❌ DO NOT: Commit secrets to Git
# Add to .gitignore:
echo ".env.prod" >> .gitignore
echo "certs/server.key" >> .gitignore
echo "secrets/" >> .gitignore

# ❌ DO NOT: Log sensitive values
# Configure log redaction in application code
```

---

## Monitoring & Troubleshooting

### Health Checks

```bash
# Check all services
for service in cloud-fl-server cloud-api cloud-analytics postgres influxdb; do
  echo "=== $service ==="
  docker compose exec $service curl http://localhost:8080/health 2>/dev/null || echo "Not responding"
done

# Detailed service status
docker compose ps
docker compose logs --tail=50
```

### Common Issues & Fixes

#### Issue: Services not starting

```bash
# Check logs
docker compose logs cloud-api

# Common causes:
# 1. Port already in use
lsof -i :8443

# 2. Insufficient disk space
df -h

# 3. Permission issues
sudo chown -R $USER:$USER .
```

#### Issue: Database connection errors

```bash
# Verify PostgreSQL is running
docker compose exec postgres psql -U ayushbot -d ayushbot_cloud -c "SELECT 1"

# Check connection string
echo $POSTGRES_URL
postgresql://ayushbot:password@postgres:5432/ayushbot_cloud

# Test connection from API container
docker compose exec cloud-api psql $POSTGRES_URL -c "SELECT 1"
```

#### Issue: TLS certificate errors

```bash
# Check certificate validity
openssl x509 -in certs/server.crt -text -noout

# Check key permissions
ls -la certs/server.key  # Should be 600

# Regenerate if needed
python generate_certs.py --output-dir ./certs --force
```

### Monitoring Metrics

```bash
# Monitor container resource usage
docker stats

# Monitor application logs (JSON format preferred)
docker compose logs --follow --timestamps

# Integration with monitoring tools
# Prometheus: http://localhost:9090 (if enabled)
# Grafana: http://localhost:3000 (if enabled)
# ELK Stack: Elasticsearch, Logstash, Kibana (if enabled)
```

---

## Backup & Disaster Recovery

### Backup Strategy

```bash
# 1. Backup PostgreSQL
docker compose exec postgres pg_dump -U ayushbot ayushbot_cloud > backup_$(date +%Y%m%d_%H%M%S).sql

# 2. Backup InfluxDB
docker compose exec influxdb influx backup /influxdb-backup

# 3. Backup model artifacts
tar -czf models_$(date +%Y%m%d_%H%M%S).tar.gz models/

# 4. Backup volumes
docker run --rm -v ayushbot-cloud_postgres-data:/data -v $(pwd):/backup \
  alpine tar -czf /backup/postgres-backup-$(date +%Y%m%d).tar.gz -C /data .
```

### Automated Backups (Cron)

```bash
# Create backup script: backup.sh
#!/bin/bash
BACKUP_DIR="/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# PostgreSQL backup
docker compose exec -T postgres pg_dump -U ayushbot ayushbot_cloud | gzip > $BACKUP_DIR/postgres_$TIMESTAMP.sql.gz

# Upload to S3
aws s3 cp $BACKUP_DIR/postgres_$TIMESTAMP.sql.gz s3://ayushbot-backups/prod/

# Cleanup old backups (keep last 30 days)
find $BACKUP_DIR -name "postgres_*.sql.gz" -mtime +30 -delete

# Add to crontab
crontab -e
# Add: 0 2 * * * /home/ubuntu/backup.sh
```

### Disaster Recovery Procedure

```bash
# 1. Stop services
docker compose down

# 2. Remove corrupted data
docker volume rm ayushbot-cloud_postgres-data ayushbot-cloud_influxdb-data

# 3. Restore from backup
docker compose up -d postgres influxdb

# 4. Restore data
docker compose exec postgres psql -U ayushbot ayushbot_cloud < backup_20260531_120000.sql

# 5. Restart remaining services
docker compose up -d
```

---

## Scaling & Performance

### Horizontal Scaling (Multiple Replicas)

```yaml
# docker-compose.prod.yml
cloud-api:
  deploy:
    replicas: 3  # Run 3 instances
    resources:
      limits:
        cpus: '1'
        memory: 1G
```

### Load Balancing

```bash
# Using Nginx (reverse proxy)
# Install Nginx
sudo apt-get install nginx

# Configure /etc/nginx/sites-available/ayushbot-cloud
upstream cloud_api {
  server localhost:8443;
  server localhost:8444;
  server localhost:8445;
}

server {
  listen 443 ssl;
  server_name cloud.ayushbot.io;
  
  ssl_certificate /etc/ssl/certs/server.crt;
  ssl_certificate_key /etc/ssl/private/server.key;
  
  location / {
    proxy_pass https://cloud_api;
  }
}
```

### Database Connection Pooling

```python
# In cloud/api/main.py
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

engine = create_engine(
    POSTGRES_URL,
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=40,
    pool_pre_ping=True
)
```

### Caching Strategy

```bash
# Add Redis for caching (optional)
# In docker-compose.yml
cache:
  image: redis:7-alpine
  ports:
    - "6379:6379"
  volumes:
    - cache-data:/data
```

---

## Security Best Practices

### 1. Network Security

```bash
# Only expose necessary ports
# Firewall rules (UFW on Ubuntu)
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp      # SSH
sudo ufw allow 8443/tcp    # API
sudo ufw allow 8501/tcp    # Dashboard
sudo ufw enable
```

### 2. Container Security

```bash
# Run containers as non-root
# Dockerfile: USER ayushbot

# Use read-only root filesystem (where possible)
# docker-compose.yml:
# security_opt:
#   - no-new-privileges:true
# read_only: true
# tmpfs: /tmp
```

### 3. Secrets Management

```bash
# ✅ Use Docker secrets or external manager
# ❌ Never hardcode passwords
# ❌ Never log sensitive values
# ❌ Never commit .env files

# Example: Docker Compose secrets
docker secret create db_password - < db_password.txt
```

### 4. TLS/HTTPS Enforcement

```bash
# Enable TLS in .env.prod
ENABLE_TLS=true
CERTFILE=/app/certs/server.crt
KEYFILE=/app/certs/server.key

# Use strong cipher suites
# Test with: nmap --script ssl-enum-ciphers -p 8443 localhost
```

### 5. Regular Updates

```bash
# Keep Docker images updated
docker pull postgres:16-alpine
docker pull influxdb:2.7-alpine

# Update OS packages
sudo apt-get update && sudo apt-get upgrade -y

# Schedule security patches
# Set cron job for automatic updates
```

---

## Rollback Procedures

### Quick Rollback (Keep Current Version)

```bash
# If the latest deployment has issues:
docker compose stop
docker compose start
```

### Full Rollback to Previous Version

```bash
# 1. Save current state
docker compose down
tar -czf backup_$(date +%Y%m%d_%H%M%S).tar.gz docker-compose.yml .env.prod certs/

# 2. Checkout previous commit
git log --oneline  # View commit history
git checkout <commit-hash>

# 3. Restore from backup (if data corrupted)
docker compose down -v
docker volume create ayushbot-cloud_postgres-data
# Restore from backup

# 4. Deploy previous version
docker compose up -d
```

### Database Rollback

```bash
# If database schema changed and caused issues:
# 1. Stop services
docker compose down

# 2. Restore database backup
docker compose up -d postgres influxdb
docker compose exec postgres psql -U ayushbot ayushbot_cloud < backup_previous.sql

# 3. Restart services
docker compose up -d
```

---

## Emergency Contacts & Support

**On-Call Support**: [Add contact information]  
**Incident Response**: [Add runbook link]  
**Status Page**: [Add status page URL]  
**Documentation**: https://github.com/varunaditya27/AyushBot/tree/main/cloud

---

## Appendix: Useful Commands

```bash
# View Docker Compose logs
docker compose logs -f                      # All services
docker compose logs -f cloud-api            # Single service
docker compose logs --tail=50 cloud-api     # Last 50 lines

# Execute commands in containers
docker compose exec cloud-api python -c "import sys; print(sys.version)"
docker compose exec postgres psql -U ayushbot -d ayushbot_cloud

# Rebuild without cache
docker compose build --no-cache

# Remove unused resources
docker system prune -a

# Check network connectivity
docker compose exec cloud-api ping postgres
docker compose exec cloud-api curl http://influxdb:8086/ping

# Performance monitoring
docker stats
docker system df

# Configuration validation
docker compose config
docker compose config --resolve-image-digests
```

---

**Document Version**: 1.0  
**Last Updated**: May 31, 2026  
**Next Review**: June 30, 2026
