# Production Deployment Guide - Robot Runner v2.0

Guía para deployment en entornos de producción.

---

## Production Checklist

- [ ] Redis instalado y configurado
- [ ] Certificados SSL válidos (no self-signed)
- [ ] `config.json` configurado correctamente
- [ ] Firewall configurado
- [ ] Monitoring configurado
- [ ] Backups configurados
- [ ] Logs rotados
- [ ] Recursos suficientes (CPU, RAM, disco)
- [ ] Auto-start configurado
- [ ] Health checks configurados

---

## Architecture Overview

```
┌─────────────────┐
│  Orquestador    │
│  (Remote)       │
└────────┬────────┘
         │ HTTPS
         ↓
┌────────────────────────────────┐
│  Robot Runner (Production)     │
│  ┌──────────────────────────┐ │
│  │ Gunicorn (4 workers)     │ │
│  │ + Celery workers         │ │
│  └──────────────────────────┘ │
│  ┌──────────────────────────┐ │
│  │ Redis (State + Queue)    │ │
│  └──────────────────────────┘ │
└────────────────────────────────┘
```

---

## Server Requirements

### Hardware (Recommended)

- **CPU**: 4+ cores
- **RAM**: 8GB
- **Disk**: 20GB SSD (sistema + logs)
- **Network**: 100 Mbps+ (para streaming)

### Software

- **OS**: Ubuntu 20.04 LTS (recommended) / macOS / Windows Server
- **Python**: 3.9+
- **Redis**: 5.0+
- **SSL**: Valid certificates from CA

---

## Installation for Production

### 1. System Setup

```bash
# Update system
sudo apt-get update && sudo apt-get upgrade -y

# Install dependencies
sudo apt-get install -y python3.9 python3.9-venv python3-pip redis-server

# Create user
sudo useradd -r -s /bin/bash -d /opt/robotrunner robotrunner
sudo mkdir -p /opt/robotrunner
sudo chown robotrunner:robotrunner /opt/robotrunner
```

### 2. Install Robot Runner

```bash
# Switch to robotrunner user
sudo su - robotrunner

# Clone repository (or copy binaries)
cd /opt/robotrunner
git clone https://github.com/your-org/robotrunner.git .

# Create venv
python3.9 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure

```bash
# Copy and edit config
cp config.json.example config.json
vim config.json
```

**Production `config.json`**:
```json
{
  "machine_id": "PROD-ROBOT-01",
  "license_key": "production-license-key",
  "token": "secure-production-token",
  "port": 5001,
  "ssl_enabled": true,
  "cert_file": "/opt/robotrunner/ssl/prod-cert.pem",
  "key_file": "/opt/robotrunner/ssl/prod-key.pem",
  "ca_cert": "/opt/robotrunner/ssl/prod-ca.pem",
  "notify_url": "https://orquestador.prod.com/api/robot-status",
  "notify_on_status_change": true,
  "log_level": "INFO",
  "log_file": "/var/log/robotrunner/server.log"
}
```

### 4. SSL Certificates

```bash
# Copy production certificates
sudo mkdir -p /opt/robotrunner/ssl
sudo cp /path/to/prod-cert.pem /opt/robotrunner/ssl/
sudo cp /path/to/prod-key.pem /opt/robotrunner/ssl/
sudo cp /path/to/prod-ca.pem /opt/robotrunner/ssl/
sudo chown -R robotrunner:robotrunner /opt/robotrunner/ssl
sudo chmod 600 /opt/robotrunner/ssl/*-key.pem
```

---

## Gunicorn Configuration

`gunicorn_config.py` (ya configurado):

```python
# Server socket
bind = '0.0.0.0:5001'
backlog = 2048

# Worker processes
workers = 4  # 2-4 x CPU cores
worker_class = 'sync'
worker_connections = 1000
timeout = 120
keepalive = 5

# SSL
certfile = 'ssl/cert.pem'
keyfile = 'ssl/key.pem'
ca_certs = 'ssl/ca-cert.pem'

# Logging
accesslog = 'logs/access.log'
errorlog = 'logs/error.log'
loglevel = 'info'

# Process naming
proc_name = 'robotrunner'

# Server mechanics
daemon = False  # Use systemd instead
pidfile = '/var/run/robotrunner/robotrunner.pid'
umask = 0o007
user = 'robotrunner'
group = 'robotrunner'

# Celery workers (via hooks)
def post_fork(server, worker):
    """Start Celery worker after Gunicorn fork."""
    from shared.celery_app.worker import start_celery_worker
    start_celery_worker()
```

---

## systemd Service

### Create Service File

`/etc/systemd/system/robotrunner.service`:

```ini
[Unit]
Description=Robot Runner Service
Documentation=https://github.com/your-org/robotrunner
After=network.target redis.service
Requires=redis.service

[Service]
Type=notify
User=robotrunner
Group=robotrunner
WorkingDirectory=/opt/robotrunner
Environment="PATH=/opt/robotrunner/venv/bin"
ExecStart=/opt/robotrunner/venv/bin/gunicorn -c gunicorn_config.py api.wsgi:app
ExecReload=/bin/kill -s HUP $MAINPID
KillMode=mixed
KillSignal=SIGQUIT
TimeoutStopSec=5
PrivateTmp=true
Restart=always
RestartSec=10

# Hardening
NoNewPrivileges=true
PrivateDevices=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/opt/robotrunner/logs /var/log/robotrunner
CapabilityBoundingSet=CAP_NET_BIND_SERVICE

[Install]
WantedBy=multi-user.target
```

### Enable and Start

```bash
sudo systemctl daemon-reload
sudo systemctl enable robotrunner
sudo systemctl start robotrunner
sudo systemctl status robotrunner
```

---

## Redis Configuration

### Production Settings

`/etc/redis/redis.conf`:

```conf
# Bind to localhost only (if on same machine)
bind 127.0.0.1 ::1

# Enable persistence
save 900 1
save 300 10
save 60 10000

# AOF for durability
appendonly yes
appendfilename "appendonly.aof"

# Memory management
maxmemory 2gb
maxmemory-policy allkeys-lru

# Security
requirepass your-redis-password

# Logging
loglevel notice
logfile /var/log/redis/redis-server.log
```

Update Robot Runner Redis connection in `shared/state/redis_client.py`:

```python
redis_client = redis.Redis(
    host='localhost',
    port=6379,
    db=0,
    password='your-redis-password',
    decode_responses=True
)
```

---

## Firewall Configuration

### UFW (Ubuntu)

```bash
# Enable firewall
sudo ufw enable

# Allow SSH
sudo ufw allow 22/tcp

# Allow Robot Runner
sudo ufw allow 5001/tcp

# Allow from specific orquestador IP only
sudo ufw allow from <orquestador-ip> to any port 5001

# Check status
sudo ufw status
```

---

## Monitoring & Health Checks

### Health Check Endpoint

Create `api/health.py`:

```python
from flask import Blueprint, jsonify

health_bp = Blueprint('health', __name__)

@health_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint (no auth required)."""
    return jsonify({
        'status': 'ok',
        'version': '2.0.0'
    }), 200
```

Register in `api/app.py`:

```python
from api.health import health_bp
app.register_blueprint(health_bp)
```

### Monitoring Script

```bash
#!/bin/bash
# /opt/robotrunner/scripts/health_check.sh

HEALTH_URL="https://localhost:5001/health"

response=$(curl -k -s -o /dev/null -w "%{http_code}" "$HEALTH_URL")

if [ "$response" = "200" ]; then
    echo "OK: Robot Runner is healthy"
    exit 0
else
    echo "CRITICAL: Robot Runner unhealthy (HTTP $response)"
    exit 2
fi
```

### Cron Job for Monitoring

```bash
# Add to crontab
*/5 * * * * /opt/robotrunner/scripts/health_check.sh || systemctl restart robotrunner
```

---

## Logging & Log Rotation

### Logrotate Configuration

`/etc/logrotate.d/robotrunner`:

```
/var/log/robotrunner/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 0640 robotrunner robotrunner
    sharedscripts
    postrotate
        systemctl reload robotrunner > /dev/null 2>&1 || true
    endscript
}
```

---

## Backups

### Redis Backup

```bash
#!/bin/bash
# /opt/robotrunner/scripts/backup_redis.sh

BACKUP_DIR="/backup/robotrunner/redis"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p "$BACKUP_DIR"
cp /var/lib/redis/dump.rdb "$BACKUP_DIR/dump_$DATE.rdb"
find "$BACKUP_DIR" -name "dump_*.rdb" -mtime +7 -delete
```

### Configuration Backup

```bash
#!/bin/bash
# Backup config.json

cp /opt/robotrunner/config.json "/backup/robotrunner/config_$(date +%Y%m%d).json"
```

---

## Performance Tuning

### Gunicorn Workers

```python
# Rule of thumb: (2 x CPU cores) + 1
workers = (2 * multiprocessing.cpu_count()) + 1
```

### Celery Concurrency

```python
# In shared/celery_app/config.py
CELERYD_CONCURRENCY = 4  # Number of concurrent tasks
```

### Redis Tuning

```conf
# Increase connections
maxclients 10000

# Tune TCP backlog
tcp-backlog 511
```

---

## Security Best Practices

### 1. Use Strong Tokens

```bash
# Generate secure token
openssl rand -hex 32
```

### 2. Restrict Access

- Use firewall to allow only orquestador IP
- Use VPN for remote access
- Never expose to public internet without additional protection

### 3. Regular Updates

```bash
# Update system
sudo apt-get update && sudo apt-get upgrade

# Update Robot Runner
cd /opt/robotrunner
git pull
pip install -r requirements.txt
sudo systemctl restart robotrunner
```

### 4. Audit Logs

```bash
# Monitor access logs
tail -f /opt/robotrunner/logs/access.log

# Check for suspicious activity
grep "403" /opt/robotrunner/logs/access.log
```

---

## Troubleshooting Production Issues

### High CPU Usage

```bash
# Check worker processes
ps aux | grep gunicorn

# Check Celery tasks
redis-cli LLEN celery

# Monitor in real-time
htop
```

### Memory Leaks

```bash
# Monitor memory usage
watch -n 1 'ps aux | grep gunicorn'

# Restart gracefully
sudo systemctl reload robotrunner
```

### Redis Out of Memory

```bash
# Check Redis memory
redis-cli INFO memory

# Clear old data
redis-cli FLUSHDB  # CAUTION: Deletes all data
```

---

## Disaster Recovery

### Recovery Plan

1. **Service Down**: Restart via systemd
2. **Redis Failure**: Restore from backup
3. **Disk Full**: Clean logs, expand disk
4. **Certificate Expired**: Renew certificates

### Recovery Steps

```bash
# 1. Stop service
sudo systemctl stop robotrunner

# 2. Restore Redis
sudo cp /backup/robotrunner/redis/dump_latest.rdb /var/lib/redis/dump.rdb
sudo chown redis:redis /var/lib/redis/dump.rdb
sudo systemctl restart redis

# 3. Restore config
sudo cp /backup/robotrunner/config_latest.json /opt/robotrunner/config.json

# 4. Start service
sudo systemctl start robotrunner
```

---

## Próximos Pasos

- Leer [Compilation Guide](compilation.md) para crear ejecutables
- Consultar [Cross-Platform Guide](cross-platform.md) para notas específicas del SO
- Ver [Architecture Docs](../architecture/overview.md) para entender el sistema

---

**Actualizado**: 2026-01-08
**Versión**: 2.0.0
