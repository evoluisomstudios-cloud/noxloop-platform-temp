# NOXLOOP Production Deployment Guide

## 🚀 Quick Start (Docker Compose)

### Prerequisites
- Docker 20.10+
- Docker Compose 2.0+
- Domain configured with DNS pointing to your server
- SSL certificate (Let's Encrypt recommended)

### 1. Initial Setup

```bash
# Clone repository
git clone https://github.com/your-org/noxloop-saas.git
cd noxloop-saas

# Copy environment template
cp .env.example .env

# Edit .env with your values
nano .env
```

### 2. Configure Environment Variables

Edit `.env` with production values:

```env
# MongoDB
MONGO_ROOT_USER=admin
MONGO_ROOT_PASSWORD=your-secure-mongodb-password

# Backend
JWT_SECRET_KEY=generate-random-64-char-string
CORS_ORIGINS=https://noxloop.pt

# Email
SMTP_ENABLED=true
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=noxloop@gmail.com
SMTP_PASSWORD=your-gmail-app-password

# Stripe
STRIPE_ENABLED=true
STRIPE_API_KEY=sk_live_xxxxx
STRIPE_WEBHOOK_SECRET=whsec_xxxxx

# OpenAI
OPENAI_API_KEY=sk-xxxxx

# URLs
APP_URL=https://noxloop.pt
BACKEND_URL=https://noxloop.pt/api
```

### 3. Deploy

```bash
# Build and start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f

# Check health
curl http://localhost:8001/api/status
curl http://localhost:3000/health
```

### 4. Configure Nginx Reverse Proxy (Production)

Create `/app/nginx/nginx.conf`:

```nginx
upstream backend {
    server backend:8001;
}

upstream frontend {
    server frontend:80;
}

server {
    listen 80;
    server_name noxloop.pt www.noxloop.pt;
    
    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name noxloop.pt www.noxloop.pt;

    # SSL Configuration
    ssl_certificate /etc/nginx/ssl/fullchain.pem;
    ssl_certificate_key /etc/nginx/ssl/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    
    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Backend API
    location /api/ {
        proxy_pass http://backend/api/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Frontend
    location / {
        proxy_pass http://frontend/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
```

Deploy with production profile:

```bash
docker-compose --profile production up -d
```

### 5. SSL Certificate (Let's Encrypt)

```bash
# Install certbot
sudo apt-get install certbot

# Generate certificate
sudo certbot certonly --standalone -d noxloop.pt -d www.noxloop.pt

# Copy certificates
sudo cp /etc/letsencrypt/live/noxloop.pt/fullchain.pem nginx/ssl/
sudo cp /etc/letsencrypt/live/noxloop.pt/privkey.pem nginx/ssl/

# Restart nginx
docker-compose restart nginx
```

### 6. Configure Stripe Webhooks

1. Go to Stripe Dashboard → Developers → Webhooks
2. Add endpoint: `https://noxloop.pt/api/billing/webhook/stripe`
3. Select events:
   - `checkout.session.completed`
   - `invoice.payment_succeeded`
   - `customer.subscription.deleted`
4. Copy webhook secret to `.env` as `STRIPE_WEBHOOK_SECRET`
5. Restart backend: `docker-compose restart backend`

## 📦 MongoDB Backup & Restore

### Automated Daily Backups

Create `/app/scripts/backup-mongo.sh`:

```bash
#!/bin/bash
BACKUP_DIR="/app/backups"
DATE=$(date +%Y%m%d_%H%M%S)
CONTAINER="noxloop-mongodb"

mkdir -p $BACKUP_DIR

docker exec $CONTAINER mongodump \
  --username admin \
  --password changeme \
  --authenticationDatabase admin \
  --db noxloop_db \
  --archive=/data/backup_$DATE.archive

docker cp $CONTAINER:/data/backup_$DATE.archive $BACKUP_DIR/

# Keep only last 7 days
find $BACKUP_DIR -name "backup_*.archive" -mtime +7 -delete

echo "Backup completed: backup_$DATE.archive"
```

Add to crontab:

```bash
crontab -e
# Add: 0 2 * * * /app/scripts/backup-mongo.sh
```

### Restore from Backup

```bash
docker exec -i noxloop-mongodb mongorestore \
  --username admin \
  --password changeme \
  --authenticationDatabase admin \
  --archive=/data/backup_20250207.archive
```

## 🔧 Maintenance

### Update Application

```bash
# Pull latest code
git pull origin main

# Rebuild containers
docker-compose build

# Restart services
docker-compose up -d

# Check logs
docker-compose logs -f backend frontend
```

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f mongodb

# Last 100 lines
docker-compose logs --tail=100 backend
```

### Restart Services

```bash
# All services
docker-compose restart

# Specific service
docker-compose restart backend
docker-compose restart frontend
```

### Scale Backend Workers

```bash
# Edit docker-compose.yml
services:
  backend:
    command: ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8001", "--workers", "4"]

# Restart
docker-compose up -d backend
```

## 🔍 Monitoring

### Health Checks

```bash
# Backend
curl https://noxloop.pt/api/status

# Frontend
curl https://noxloop.pt/health

# MongoDB
docker exec noxloop-mongodb mongosh --eval "db.adminCommand('ping')"
```

### Resource Usage

```bash
# Container stats
docker stats

# Disk usage
docker system df

# Clean unused resources
docker system prune -a
```

## 🚨 Troubleshooting

### Backend Won't Start

```bash
# Check logs
docker-compose logs backend

# Common issues:
# 1. MongoDB not ready → Wait 30s, restart backend
# 2. Missing env vars → Check .env file
# 3. Port conflict → Change port in docker-compose.yml
```

### Frontend Build Fails

```bash
# Clear node_modules
docker-compose run --rm frontend sh -c "rm -rf node_modules && yarn install"

# Rebuild
docker-compose build frontend
docker-compose up -d frontend
```

### Database Connection Issues

```bash
# Check MongoDB logs
docker-compose logs mongodb

# Test connection
docker exec -it noxloop-mongodb mongosh \
  -u admin -p changeme --authenticationDatabase admin
```

## 📊 Performance Tuning

### MongoDB Indexes

```bash
docker exec -it noxloop-mongodb mongosh -u admin -p changeme --authenticationDatabase admin

use noxloop_db

# Create indexes
db.users.createIndex({"email": 1}, {unique: true})
db.workspaces.createIndex({"owner_id": 1})
db.products.createIndex({"workspace_id": 1, "is_published": 1})
db.purchases.createIndex({"user_id": 1, "status": 1})
db.payments.createIndex({"user_id": 1, "created_at": -1})
```

### Backend Workers

For production, increase workers:
```yaml
command: ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8001", "--workers", "4"]
```

### Nginx Caching

Add to nginx config:
```nginx
proxy_cache_path /var/cache/nginx levels=1:2 keys_zone=api_cache:10m max_size=100m inactive=60m;

location /api/ {
    proxy_cache api_cache;
    proxy_cache_valid 200 5m;
    proxy_cache_methods GET HEAD;
    # ... rest of proxy config
}
```

## 🔐 Security Checklist

- [ ] Change all default passwords
- [ ] Use strong JWT_SECRET_KEY (64+ characters)
- [ ] Enable SSL/TLS (HTTPS)
- [ ] Configure firewall (UFW/iptables)
- [ ] Enable Stripe webhook signatures
- [ ] Set up automated backups
- [ ] Configure log rotation
- [ ] Enable rate limiting (nginx)
- [ ] Set up monitoring/alerts
- [ ] Regular security updates

## 📞 Support

For issues or questions:
- GitHub Issues: https://github.com/your-org/noxloop-saas/issues
- Email: support@noxloop.pt
- Documentation: https://docs.noxloop.pt

## 📝 License

© 2025 NOXLOOP. All rights reserved.
