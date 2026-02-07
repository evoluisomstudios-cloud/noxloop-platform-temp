# DigiForge - Guia Completo de Self-Hosting (€0/mês)

**Versão:** 2.0.0  
**Objetivo:** Deploy completo num servidor próprio sem custos mensais

---

## 1. Pré-requisitos

### Hardware Mínimo
| Requisito | Mínimo | Recomendado |
|-----------|--------|-------------|
| RAM | 2 GB | 4 GB |
| CPU | 2 cores | 4 cores |
| Disco | 20 GB | 50 GB SSD |
| OS | Ubuntu 22.04 LTS | Ubuntu 22.04 LTS |

### Software Necessário
- Docker + Docker Compose
- Nginx (reverse proxy)
- Certbot (SSL)
- UFW (firewall)

---

## 2. Instalação do Sistema Base

```bash
# Atualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar dependências
sudo apt install -y curl git ufw fail2ban nginx certbot python3-certbot-nginx

# Instalar Docker
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER

# Instalar Docker Compose
sudo apt install -y docker-compose-plugin

# Verificar
docker --version
docker compose version

# IMPORTANTE: Logout e login para aplicar grupo docker
```

---

## 3. Configurar Firewall (UFW)

```bash
# Configurar regras
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp comment 'SSH'
sudo ufw allow 80/tcp comment 'HTTP'
sudo ufw allow 443/tcp comment 'HTTPS'

# Ativar
sudo ufw enable

# Verificar
sudo ufw status verbose
```

---

## 4. Configurar Fail2ban (Proteção SSH)

```bash
# Criar configuração
sudo tee /etc/fail2ban/jail.local << 'EOF'
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 5

[sshd]
enabled = true
port = 22
filter = sshd
logpath = /var/log/auth.log
maxretry = 3
EOF

# Reiniciar
sudo systemctl restart fail2ban
sudo systemctl enable fail2ban

# Verificar status
sudo fail2ban-client status sshd
```

---

## 5. Configurar DNS

### Opção A: Domínio Próprio (Cloudflare)

1. Acede ao [Cloudflare Dashboard](https://dash.cloudflare.com)
2. Adiciona registos DNS:

| Tipo | Nome | Conteúdo | Proxy |
|------|------|----------|-------|
| A | digiforge | TEU_IP_PUBLICO | DNS only |
| A | api.digiforge | TEU_IP_PUBLICO | DNS only |

> Desativar proxy (laranja → cinzento) para Let's Encrypt funcionar.

### Opção B: DuckDNS (Grátis)

1. Acede a [duckdns.org](https://www.duckdns.org)
2. Cria subdomínio: `digiforge` → `digiforge.duckdns.org`
3. Configura atualização automática de IP:

```bash
mkdir -p /opt/duckdns
cat > /opt/duckdns/duck.sh << 'EOF'
#!/bin/bash
curl -s "https://www.duckdns.org/update?domains=digiforge&token=TEU_TOKEN&ip="
EOF
chmod +x /opt/duckdns/duck.sh
(crontab -l 2>/dev/null; echo "*/5 * * * * /opt/duckdns/duck.sh >/dev/null 2>&1") | crontab -
```

---

## 6. Instalar Aplicação

```bash
# Criar diretório
sudo mkdir -p /opt/digiforge
sudo chown $USER:$USER /opt/digiforge
cd /opt/digiforge

# Clonar repositório
git clone https://github.com/daremoservice/digiforge-saas.git .

# Criar .env de produção
cat > .env << 'EOF'
DOMAIN=digiforge.teudominio.com
API_DOMAIN=api.digiforge.teudominio.com
JWT_SECRET_KEY=GERAR_COM_openssl_rand_hex_32
ADMIN_EMAIL=admin@teudominio.com
ADMIN_PASSWORD=SenhaSegura123!
LLM_PROVIDER=mock
STRIPE_ENABLED=false
RAG_ENABLED=false
EOF

# Gerar JWT secret
JWT_KEY=$(openssl rand -hex 32)
sed -i "s/GERAR_COM_openssl_rand_hex_32/$JWT_KEY/" .env

# Criar backend/.env
cat > backend/.env << 'EOF'
MONGO_URL=mongodb://mongodb:27017
DB_NAME=digiforge
CORS_ORIGINS=*
EOF

# Build e iniciar
docker compose -f docker-compose.prod.yml build
docker compose -f docker-compose.prod.yml up -d
```

---

## 7. Configurar Nginx (Reverse Proxy)

```bash
# Criar configuração
sudo tee /etc/nginx/sites-available/digiforge << 'EOF'
# Frontend
server {
    listen 80;
    server_name digiforge.teudominio.com;

    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }
}

# API Backend
server {
    listen 80;
    server_name api.digiforge.teudominio.com;

    location / {
        proxy_pass http://127.0.0.1:8001;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF

# Ativar site
sudo ln -sf /etc/nginx/sites-available/digiforge /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Testar e reiniciar
sudo nginx -t
sudo systemctl restart nginx
```

---

## 8. Configurar SSL (Let's Encrypt)

```bash
# Obter certificados
sudo certbot --nginx -d digiforge.teudominio.com -d api.digiforge.teudominio.com --non-interactive --agree-tos -m teu@email.com

# Renovação automática já configurada via systemd timer
sudo systemctl status certbot.timer

# Testar renovação
sudo certbot renew --dry-run
```

---

## 9. Backups Automáticos

```bash
# Criar diretório
sudo mkdir -p /opt/backups/digiforge
sudo chown $USER:$USER /opt/backups/digiforge

# Criar script
cat > /opt/digiforge/backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/opt/backups/digiforge"
DATE=$(date +%Y%m%d_%H%M%S)

docker exec digiforge-mongodb mongodump --out /backup --quiet
docker cp digiforge-mongodb:/backup "$BACKUP_DIR/mongodb_$DATE"
cd "$BACKUP_DIR"
tar -czf "backup_$DATE.tar.gz" "mongodb_$DATE"
rm -rf "mongodb_$DATE"
docker exec digiforge-mongodb rm -rf /backup
find "$BACKUP_DIR" -name "backup_*.tar.gz" -mtime +30 -delete
echo "[$(date)] Backup: backup_$DATE.tar.gz"
EOF
chmod +x /opt/digiforge/backup.sh

# Agendar backup diário às 3:00
(crontab -l 2>/dev/null; echo "0 3 * * * /opt/digiforge/backup.sh >> /var/log/digiforge-backup.log 2>&1") | crontab -
```

### Restaurar Backup

```bash
cd /opt/backups/digiforge
tar -xzf backup_YYYYMMDD_HHMMSS.tar.gz
docker cp mongodb_YYYYMMDD_HHMMSS digiforge-mongodb:/restore
docker exec digiforge-mongodb mongorestore /restore --drop
docker exec digiforge-mongodb rm -rf /restore
```

---

## 10. Atualização e Rollback

### Atualizar

```bash
cd /opt/digiforge

# Backup primeiro
./backup.sh

# Guardar versão atual
git rev-parse HEAD > .last_commit

# Atualizar
git pull origin main
docker compose -f docker-compose.prod.yml build
docker compose -f docker-compose.prod.yml up -d
```

### Rollback

```bash
cd /opt/digiforge
git checkout $(cat .last_commit)
docker compose -f docker-compose.prod.yml build
docker compose -f docker-compose.prod.yml up -d
```

---

## 11. Comandos Úteis

```bash
# Status
docker compose -f docker-compose.prod.yml ps

# Logs
docker compose -f docker-compose.prod.yml logs -f

# Reiniciar
docker compose -f docker-compose.prod.yml restart

# Health check
curl https://api.teudominio.com/api/status

# Ver recursos
docker stats --no-stream
```

---

## 12. Custos

| Item | Custo |
|------|-------|
| Servidor (casa) | €0 (eletricidade ~€2-5) |
| DuckDNS | €0 |
| Let's Encrypt | €0 |
| OpenAI (opcional) | €0-20/mês |
| **TOTAL** | **€0-5/mês** |

---

## 13. Checklist de Produção

- [ ] UFW ativo (portas 22, 80, 443)
- [ ] Fail2ban configurado
- [ ] SSL funcionando (HTTPS)
- [ ] JWT_SECRET_KEY único gerado
- [ ] ADMIN_PASSWORD alterado
- [ ] Backups automáticos configurados
- [ ] API respondendo em /api/status
- [ ] Frontend carregando

```bash
# Verificar tudo
curl -I https://digiforge.teudominio.com
curl https://api.digiforge.teudominio.com/api/status
```
