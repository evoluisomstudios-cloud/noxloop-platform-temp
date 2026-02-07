# DigiForge - Guia de Deployment para Produção (€0/mês)

**Versão:** 2.0.0  
**Data:** Fevereiro 2026  
**Objetivo:** Deploy completo num servidor doméstico Linux com €0 de custos mensais

---

## 1. Arquitetura do Sistema

```
┌─────────────────────────────────────────────────────────────────────────┐
│                            INTERNET                                      │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         ROUTER (Port Forward)                            │
│                         80 → Server:80                                   │
│                         443 → Server:443                                 │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                     HOME SERVER (Ubuntu 22.04)                           │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │                      UFW Firewall                                   │ │
│  │                   22/tcp, 80/tcp, 443/tcp                          │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                                    │                                     │
│                                    ▼                                     │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │              CADDY (Reverse Proxy + Auto-SSL)                       │ │
│  │                    :443 → HTTPS                                     │ │
│  │                    :80 → redirect HTTPS                             │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                          │              │                                │
│                          ▼              ▼                                │
│  ┌──────────────────────────┐  ┌──────────────────────────┐             │
│  │   digiforge-frontend     │  │    digiforge-backend     │             │
│  │   (React + Nginx)        │  │    (FastAPI + Uvicorn)   │             │
│  │   Container :3000        │  │    Container :8001       │             │
│  └──────────────────────────┘  └──────────────────────────┘             │
│                                         │                                │
│                                         ▼                                │
│                          ┌──────────────────────────┐                   │
│                          │   digiforge-mongodb      │                   │
│                          │   (MongoDB 6.0)          │                   │
│                          │   Container :27017       │                   │
│                          │   Volume: mongodb_data   │                   │
│                          └──────────────────────────┘                   │
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │                    DOCKER VOLUMES                                   │ │
│  │   mongodb_data    → /var/lib/docker/volumes/mongodb_data           │ │
│  │   caddy_data      → /var/lib/docker/volumes/caddy_data             │ │
│  │   caddy_config    → /var/lib/docker/volumes/caddy_config           │ │
│  │   backend_exports → /var/lib/docker/volumes/backend_exports        │ │
│  └────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Pré-requisitos

| Requisito | Mínimo | Recomendado |
|-----------|--------|-------------|
| RAM | 2 GB | 4 GB |
| CPU | 2 cores | 4 cores |
| Disco | 20 GB SSD | 50 GB SSD |
| OS | Ubuntu 22.04 LTS | Ubuntu 22.04 LTS |
| IP Público | Sim (dinâmico OK) | Sim |
| Porta 80/443 | Aberta no router | Aberta |

---

## 3. Configuração DNS

### Opção A: Cloudflare (se tens domínio próprio) - RECOMENDADO

1. Acede a [dash.cloudflare.com](https://dash.cloudflare.com)
2. Seleciona o teu domínio
3. Vai a **DNS** → **Records**
4. Adiciona os seguintes registos:

| Tipo | Nome | Conteúdo | Proxy | TTL |
|------|------|----------|-------|-----|
| A | digiforge | `TEU_IP_PUBLICO` | DNS only (cinzento) | Auto |
| A | api.digiforge | `TEU_IP_PUBLICO` | DNS only (cinzento) | Auto |

> **IMPORTANTE:** Desativa o proxy (ícone laranja → cinzento) para permitir Let's Encrypt funcionar.

Para obter o teu IP público:
```bash
curl -s ifconfig.me
```

### Opção B: DuckDNS (grátis, sem domínio)

1. Acede a [duckdns.org](https://www.duckdns.org) e faz login com Google/GitHub
2. Cria um subdomínio: `digiforge` (ficará `digiforge.duckdns.org`)
3. Aponta para o teu IP público
4. Guarda o **token** que aparece

```bash
# Criar script de atualização automática de IP
mkdir -p /opt/duckdns
cat > /opt/duckdns/duck.sh << 'EOF'
#!/bin/bash
DOMAIN="digiforge"
TOKEN="TEU_TOKEN_DUCKDNS"
curl -s "https://www.duckdns.org/update?domains=$DOMAIN&token=$TOKEN&ip="
EOF
chmod +x /opt/duckdns/duck.sh

# Cron para atualizar IP a cada 5 minutos
(crontab -l 2>/dev/null; echo "*/5 * * * * /opt/duckdns/duck.sh >/dev/null 2>&1") | crontab -
```

**Domínios resultantes:**
- DuckDNS: `digiforge.duckdns.org` (frontend + API no mesmo)
- Cloudflare: `digiforge.teudominio.com` + `api.digiforge.teudominio.com`

---

## 4. Instalação Passo-a-Passo

### 4.1 Preparar o Sistema

```bash
# Atualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar dependências
sudo apt install -y curl git ufw

# Instalar Docker (método oficial)
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER

# Instalar Docker Compose plugin
sudo apt install -y docker-compose-plugin

# Verificar instalação
docker --version
docker compose version

# IMPORTANTE: Fazer logout e login para aplicar grupo docker
# Ou executar: newgrp docker
```

### 4.2 Configurar Firewall

```bash
# Configurar UFW
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp comment 'SSH'
sudo ufw allow 80/tcp comment 'HTTP'
sudo ufw allow 443/tcp comment 'HTTPS'

# Ativar firewall
sudo ufw enable

# Verificar estado
sudo ufw status verbose
```

**Output esperado:**
```
Status: active
To                         Action      From
--                         ------      ----
22/tcp                     ALLOW IN    Anywhere
80/tcp                     ALLOW IN    Anywhere
443/tcp                    ALLOW IN    Anywhere
```

### 4.3 Configurar Port Forwarding no Router

No painel de administração do teu router (geralmente `192.168.1.1`):

| Porta Externa | Porta Interna | Protocolo | IP Destino |
|---------------|---------------|-----------|------------|
| 80 | 80 | TCP | IP_DO_SERVIDOR |
| 443 | 443 | TCP | IP_DO_SERVIDOR |

> Para descobrir o IP interno do servidor: `hostname -I | awk '{print $1}'`

### 4.4 Clonar o Repositório

```bash
# Criar diretório de aplicações
sudo mkdir -p /opt/digiforge
sudo chown $USER:$USER /opt/digiforge
cd /opt/digiforge

# Clonar repositório
git clone https://github.com/daremoservice/digiforge-saas.git .

# Verificar estrutura
ls -la
```

### 4.5 Criar Ficheiros de Configuração

#### Criar `.env` na raiz (para Docker Compose)

```bash
cat > /opt/digiforge/.env << 'EOF'
# ============================================
# DigiForge Production Environment
# ============================================

# === DOMÍNIO (escolhe UM) ===
# Opção Cloudflare:
DOMAIN=digiforge.teudominio.com
API_DOMAIN=api.digiforge.teudominio.com

# Opção DuckDNS (descomenta e comenta acima):
# DOMAIN=digiforge.duckdns.org
# API_DOMAIN=digiforge.duckdns.org

# === SEGURANÇA ===
# GERAR NOVO: openssl rand -hex 32
JWT_SECRET_KEY=GERA_UMA_CHAVE_AQUI_COM_OPENSSL_RAND_HEX_32

# === ADMIN ===
ADMIN_EMAIL=admin@teudominio.com
ADMIN_PASSWORD=SenhaSegura123!

# === LLM PROVIDER ===
# Opções: mock (default), openai, local_llm
LLM_PROVIDER=mock
OPENAI_API_KEY=
OPENAI_MODEL=gpt-4o

# === LOCAL LLM (opcional) ===
LOCAL_LLM_BASE_URL=http://192.168.1.214:5002
LOCAL_LLM_API_KEY=not-needed
LOCAL_LLM_MODEL=llama3

# === RAG (opcional) ===
RAG_ENABLED=false
RAG_BASE_URL=http://192.168.1.211:8811

# === WEBHOOKS N8N (opcional) ===
N8N_WEBHOOK_ENABLED=false
N8N_WEBHOOK_URL=

# === STRIPE (opcional) ===
# Taxa: 1.4% + €0.25 por transação
STRIPE_ENABLED=false
STRIPE_API_KEY=
STRIPE_WEBHOOK_SECRET=

# === GOOGLE OAUTH (opcional) ===
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
EOF
```

**IMPORTANTE:** Gera uma chave JWT única:
```bash
JWT_KEY=$(openssl rand -hex 32)
sed -i "s/GERA_UMA_CHAVE_AQUI_COM_OPENSSL_RAND_HEX_32/$JWT_KEY/" /opt/digiforge/.env
echo "JWT Key gerada: $JWT_KEY"
```

#### Criar `backend/.env`

```bash
cat > /opt/digiforge/backend/.env << 'EOF'
MONGO_URL=mongodb://mongodb:27017
DB_NAME=digiforge
CORS_ORIGINS=*
EOF
```

### 4.6 Criar Caddyfile

```bash
cat > /opt/digiforge/Caddyfile << 'EOF'
# ============================================
# DigiForge Caddy Configuration
# Automatic HTTPS via Let's Encrypt
# ============================================

# Opção 1: Domínios separados (Cloudflare)
{$DOMAIN} {
    encode gzip
    
    # Security headers
    header {
        X-Content-Type-Options "nosniff"
        X-Frame-Options "SAMEORIGIN"
        X-XSS-Protection "1; mode=block"
        Referrer-Policy "strict-origin-when-cross-origin"
        -Server
    }
    
    # Frontend
    reverse_proxy digiforge-frontend:80
}

{$API_DOMAIN} {
    encode gzip
    
    # Security headers
    header {
        X-Content-Type-Options "nosniff"
        X-Frame-Options "SAMEORIGIN"
        X-XSS-Protection "1; mode=block"
        Referrer-Policy "strict-origin-when-cross-origin"
        -Server
    }
    
    # Backend API
    reverse_proxy digiforge-backend:8001
}

# Opção 2: DuckDNS (mesmo domínio, path-based routing)
# Descomenta abaixo se usares DuckDNS e comenta acima
#
# {$DOMAIN} {
#     encode gzip
#     
#     header {
#         X-Content-Type-Options "nosniff"
#         X-Frame-Options "SAMEORIGIN"
#         X-XSS-Protection "1; mode=block"
#         -Server
#     }
#     
#     # API routes
#     handle /api/* {
#         reverse_proxy digiforge-backend:8001
#     }
#     
#     # Frontend (default)
#     handle {
#         reverse_proxy digiforge-frontend:80
#     }
# }
EOF
```

### 4.7 Criar docker-compose.prod.yml

```bash
cat > /opt/digiforge/docker-compose.prod.yml << 'EOF'
version: '3.8'

# ============================================
# DigiForge Production Stack
# ============================================

services:
  # ========== REVERSE PROXY ==========
  caddy:
    image: caddy:2-alpine
    container_name: digiforge-caddy
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    environment:
      - DOMAIN=${DOMAIN}
      - API_DOMAIN=${API_DOMAIN}
    volumes:
      - ./Caddyfile:/etc/caddy/Caddyfile:ro
      - caddy_data:/data
      - caddy_config:/config
    depends_on:
      - frontend
      - backend
    networks:
      - digiforge-network

  # ========== DATABASE ==========
  mongodb:
    image: mongo:6.0
    container_name: digiforge-mongodb
    restart: unless-stopped
    volumes:
      - mongodb_data:/data/db
    environment:
      - MONGO_INITDB_DATABASE=digiforge
    networks:
      - digiforge-network
    healthcheck:
      test: echo 'db.runCommand("ping").ok' | mongosh localhost:27017/digiforge --quiet
      interval: 30s
      timeout: 10s
      retries: 5
      start_period: 40s

  # ========== BACKEND ==========
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: digiforge-backend
    restart: unless-stopped
    volumes:
      - backend_exports:/app/exports
    environment:
      # Database
      - MONGO_URL=mongodb://mongodb:27017
      - DB_NAME=digiforge
      # Security
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}
      - ADMIN_EMAIL=${ADMIN_EMAIL}
      - ADMIN_PASSWORD=${ADMIN_PASSWORD}
      # LLM
      - LLM_PROVIDER=${LLM_PROVIDER:-mock}
      - OPENAI_API_KEY=${OPENAI_API_KEY:-}
      - OPENAI_MODEL=${OPENAI_MODEL:-gpt-4o}
      - LOCAL_LLM_BASE_URL=${LOCAL_LLM_BASE_URL:-}
      - LOCAL_LLM_API_KEY=${LOCAL_LLM_API_KEY:-}
      - LOCAL_LLM_MODEL=${LOCAL_LLM_MODEL:-}
      # RAG
      - RAG_ENABLED=${RAG_ENABLED:-false}
      - RAG_BASE_URL=${RAG_BASE_URL:-}
      # Webhooks
      - N8N_WEBHOOK_ENABLED=${N8N_WEBHOOK_ENABLED:-false}
      - N8N_WEBHOOK_URL=${N8N_WEBHOOK_URL:-}
      # Stripe
      - STRIPE_ENABLED=${STRIPE_ENABLED:-false}
      - STRIPE_API_KEY=${STRIPE_API_KEY:-}
      - STRIPE_WEBHOOK_SECRET=${STRIPE_WEBHOOK_SECRET:-}
      # Google OAuth
      - GOOGLE_CLIENT_ID=${GOOGLE_CLIENT_ID:-}
      - GOOGLE_CLIENT_SECRET=${GOOGLE_CLIENT_SECRET:-}
      # CORS
      - CORS_ORIGINS=*
    depends_on:
      mongodb:
        condition: service_healthy
    networks:
      - digiforge-network
    healthcheck:
      test: curl -f http://localhost:8001/api/status || exit 1
      interval: 30s
      timeout: 10s
      retries: 3

  # ========== FRONTEND ==========
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
      args:
        # Para DuckDNS (mesmo domínio): https://${DOMAIN}/api
        # Para Cloudflare (domínios separados): https://${API_DOMAIN}
        - REACT_APP_BACKEND_URL=https://${API_DOMAIN}
    container_name: digiforge-frontend
    restart: unless-stopped
    depends_on:
      - backend
    networks:
      - digiforge-network

# ========== VOLUMES ==========
volumes:
  mongodb_data:
    driver: local
  caddy_data:
    driver: local
  caddy_config:
    driver: local
  backend_exports:
    driver: local

# ========== NETWORKS ==========
networks:
  digiforge-network:
    driver: bridge
EOF
```

### 4.8 Build e Deploy

```bash
cd /opt/digiforge

# Build das imagens
docker compose -f docker-compose.prod.yml build

# Iniciar em background
docker compose -f docker-compose.prod.yml up -d

# Verificar logs
docker compose -f docker-compose.prod.yml logs -f

# (Ctrl+C para sair dos logs)
```

---

## 5. Volumes e Backups

### 5.1 Localização dos Dados

| Volume | Conteúdo | Importância |
|--------|----------|-------------|
| `mongodb_data` | Base de dados | **CRÍTICO** |
| `caddy_data` | Certificados SSL | Importante |
| `caddy_config` | Config Caddy | Baixa |
| `backend_exports` | Exports temporários | Baixa |

### 5.2 Script de Backup Automático

```bash
# Criar diretório de backups
sudo mkdir -p /opt/backups/digiforge
sudo chown $USER:$USER /opt/backups/digiforge

# Criar script de backup
cat > /opt/digiforge/backup.sh << 'EOF'
#!/bin/bash
# ============================================
# DigiForge Backup Script
# ============================================

BACKUP_DIR="/opt/backups/digiforge"
DATE=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=30

echo "[$(date)] Starting backup..."

# Backup MongoDB
docker exec digiforge-mongodb mongodump --out /backup --quiet
docker cp digiforge-mongodb:/backup "$BACKUP_DIR/mongodb_$DATE"

# Comprimir
cd "$BACKUP_DIR"
tar -czf "digiforge_backup_$DATE.tar.gz" "mongodb_$DATE"
rm -rf "mongodb_$DATE"

# Limpar dentro do container
docker exec digiforge-mongodb rm -rf /backup

# Remover backups antigos
find "$BACKUP_DIR" -name "digiforge_backup_*.tar.gz" -mtime +$RETENTION_DAYS -delete

echo "[$(date)] Backup completed: digiforge_backup_$DATE.tar.gz"
echo "[$(date)] Size: $(du -h $BACKUP_DIR/digiforge_backup_$DATE.tar.gz | cut -f1)"
EOF

chmod +x /opt/digiforge/backup.sh

# Agendar backup diário às 3:00 AM
(crontab -l 2>/dev/null; echo "0 3 * * * /opt/digiforge/backup.sh >> /var/log/digiforge-backup.log 2>&1") | crontab -
```

### 5.3 Restaurar Backup

```bash
# Parar serviços
cd /opt/digiforge
docker compose -f docker-compose.prod.yml stop backend

# Extrair backup
cd /opt/backups/digiforge
tar -xzf digiforge_backup_YYYYMMDD_HHMMSS.tar.gz

# Restaurar MongoDB
docker cp mongodb_YYYYMMDD_HHMMSS digiforge-mongodb:/restore
docker exec digiforge-mongodb mongorestore /restore --drop
docker exec digiforge-mongodb rm -rf /restore

# Reiniciar
cd /opt/digiforge
docker compose -f docker-compose.prod.yml start backend
```

---

## 6. Logs e Monitorização

### 6.1 Ver Logs

```bash
cd /opt/digiforge

# Todos os serviços
docker compose -f docker-compose.prod.yml logs -f

# Apenas backend
docker compose -f docker-compose.prod.yml logs -f backend

# Apenas erros
docker compose -f docker-compose.prod.yml logs -f backend 2>&1 | grep -i error

# Últimas 100 linhas
docker compose -f docker-compose.prod.yml logs --tail=100 backend
```

### 6.2 Monitorização Básica

```bash
# Criar script de health check
cat > /opt/digiforge/healthcheck.sh << 'EOF'
#!/bin/bash
# ============================================
# DigiForge Health Check
# ============================================

API_URL="https://digiforge.teudominio.com/api/status"  # Ajustar domínio!

echo "=== DigiForge Health Check ==="
echo "Data: $(date)"
echo ""

# Verificar containers
echo "=== Docker Containers ==="
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep digiforge

echo ""

# Verificar API
echo "=== API Status ==="
RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" "$API_URL" 2>/dev/null)
HTTP_CODE=$(echo "$RESPONSE" | grep "HTTP_CODE" | cut -d: -f2)
BODY=$(echo "$RESPONSE" | grep -v "HTTP_CODE")

if [ "$HTTP_CODE" = "200" ]; then
    echo "✅ API OK (HTTP $HTTP_CODE)"
    echo "$BODY" | python3 -m json.tool 2>/dev/null || echo "$BODY"
else
    echo "❌ API FAILED (HTTP $HTTP_CODE)"
fi

echo ""

# Uso de recursos
echo "=== Resource Usage ==="
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}" | grep digiforge

echo ""

# Espaço em disco
echo "=== Disk Usage ==="
df -h / | tail -1
docker system df
EOF

chmod +x /opt/digiforge/healthcheck.sh
```

### 6.3 Alertas Simples (opcional)

```bash
# Adicionar ao crontab para verificar a cada 5 minutos
cat > /opt/digiforge/alert.sh << 'EOF'
#!/bin/bash
API_URL="https://digiforge.teudominio.com/api/status"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$API_URL" 2>/dev/null)

if [ "$HTTP_CODE" != "200" ]; then
    echo "[$(date)] ALERT: DigiForge API down (HTTP $HTTP_CODE)" >> /var/log/digiforge-alerts.log
    # Opcional: enviar email, telegram, etc.
fi
EOF

chmod +x /opt/digiforge/alert.sh
(crontab -l 2>/dev/null; echo "*/5 * * * * /opt/digiforge/alert.sh") | crontab -
```

---

## 7. Atualização e Rollback

### 7.1 Atualizar Aplicação

```bash
cd /opt/digiforge

# Fazer backup primeiro
./backup.sh

# Guardar versão atual (para rollback)
git rev-parse HEAD > .last_working_commit

# Puxar atualizações
git pull origin main

# Rebuild e restart
docker compose -f docker-compose.prod.yml build
docker compose -f docker-compose.prod.yml up -d

# Verificar
./healthcheck.sh
```

### 7.2 Rollback

```bash
cd /opt/digiforge

# Voltar ao commit anterior
LAST_COMMIT=$(cat .last_working_commit)
git checkout $LAST_COMMIT

# Rebuild
docker compose -f docker-compose.prod.yml build
docker compose -f docker-compose.prod.yml up -d

# Verificar
./healthcheck.sh
```

---

## 8. Configuração do Primeiro Cliente

### 8.1 Criar Utilizador Admin

```bash
# Registar admin via API
cd /opt/digiforge
API_URL="https://api.digiforge.teudominio.com"  # Ajustar!

curl -X POST "$API_URL/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@teudominio.com",
    "password": "SenhaSegura123!",
    "name": "Administrador"
  }'
```

### 8.2 Promover a Admin via MongoDB

```bash
# Aceder ao MongoDB
docker exec -it digiforge-mongodb mongosh digiforge

# No shell do MongoDB, executar:
db.users.updateOne(
  { email: "admin@teudominio.com" },
  { $set: { is_admin: true } }
)

# Verificar
db.users.findOne({ email: "admin@teudominio.com" })

# Sair
exit
```

### 8.3 Adicionar Créditos ao Workspace

```bash
docker exec -it digiforge-mongodb mongosh digiforge

# Dar 1000 créditos ao workspace do admin
db.workspaces.updateOne(
  {},  // primeiro workspace
  { 
    $set: { 
      credits: 1000,
      plan: "enterprise"
    } 
  }
)

# Verificar
db.workspaces.find().pretty()

exit
```

### 8.4 Gestão de Planos (Sem Stripe)

Para clientes que pagam manualmente (MBWay, PayPal, transferência):

```bash
docker exec -it digiforge-mongodb mongosh digiforge

# Exemplo: Dar plano Pro ao utilizador cliente@exemplo.com
# 1. Encontrar o user_id
db.users.findOne({ email: "cliente@exemplo.com" })

# 2. Encontrar o workspace do cliente
db.workspace_members.findOne({ user_id: "user_XXXX" })

# 3. Atualizar o workspace
db.workspaces.updateOne(
  { workspace_id: "ws_XXXX" },
  { 
    $set: { 
      plan: "pro",
      credits: 200  // créditos mensais do plano Pro
    } 
  }
)

exit
```

**Planos disponíveis e créditos:**

| Plano | Créditos | Preço Sugerido |
|-------|----------|----------------|
| free | 10 | €0 |
| starter | 50 | €9.99/mês |
| pro | 200 | €29.99/mês |
| enterprise | 1000 | €99.99/mês |

### 8.5 Script de Gestão de Clientes

```bash
cat > /opt/digiforge/manage_customer.sh << 'EOF'
#!/bin/bash
# ============================================
# DigiForge Customer Management
# ============================================

ACTION=$1
EMAIL=$2
PLAN=$3
CREDITS=$4

case $ACTION in
  add-credits)
    docker exec digiforge-mongodb mongosh digiforge --eval "
      var user = db.users.findOne({email: '$EMAIL'});
      if (user) {
        var membership = db.workspace_members.findOne({user_id: user.user_id});
        if (membership) {
          db.workspaces.updateOne(
            {workspace_id: membership.workspace_id},
            {\$inc: {credits: $CREDITS}}
          );
          print('Added $CREDITS credits to ' + '$EMAIL');
        }
      } else {
        print('User not found: $EMAIL');
      }
    "
    ;;
    
  set-plan)
    docker exec digiforge-mongodb mongosh digiforge --eval "
      var user = db.users.findOne({email: '$EMAIL'});
      if (user) {
        var membership = db.workspace_members.findOne({user_id: user.user_id});
        if (membership) {
          var planCredits = {free: 10, starter: 50, pro: 200, enterprise: 1000};
          db.workspaces.updateOne(
            {workspace_id: membership.workspace_id},
            {\$set: {plan: '$PLAN', credits: planCredits['$PLAN'] || 10}}
          );
          print('Set plan $PLAN for ' + '$EMAIL');
        }
      } else {
        print('User not found: $EMAIL');
      }
    "
    ;;
    
  info)
    docker exec digiforge-mongodb mongosh digiforge --eval "
      var user = db.users.findOne({email: '$EMAIL'}, {password: 0});
      if (user) {
        print('User: ' + JSON.stringify(user));
        var membership = db.workspace_members.findOne({user_id: user.user_id});
        if (membership) {
          var ws = db.workspaces.findOne({workspace_id: membership.workspace_id});
          print('Workspace: ' + JSON.stringify(ws));
        }
      } else {
        print('User not found: $EMAIL');
      }
    "
    ;;
    
  *)
    echo "Usage:"
    echo "  $0 add-credits EMAIL AMOUNT"
    echo "  $0 set-plan EMAIL PLAN  (free/starter/pro/enterprise)"
    echo "  $0 info EMAIL"
    ;;
esac
EOF

chmod +x /opt/digiforge/manage_customer.sh
```

**Uso:**
```bash
# Ver info de um cliente
./manage_customer.sh info cliente@exemplo.com

# Adicionar 50 créditos
./manage_customer.sh add-credits cliente@exemplo.com 50

# Definir plano Pro
./manage_customer.sh set-plan cliente@exemplo.com pro
```

---

## 9. Pagamentos Manuais (Alternativa ao Stripe)

### 9.1 Workflow de Pagamento Manual

1. **Cliente contacta-te** (email, WhatsApp, etc.)
2. **Envias link de pagamento:**
   - MBWay: teu número de telefone
   - PayPal: https://paypal.me/teuusername
   - Transferência: IBAN
   - Revolut: @teuusername

3. **Cliente paga e envia comprovativo**

4. **Tu ativas o plano:**
```bash
./manage_customer.sh set-plan cliente@exemplo.com pro
```

### 9.2 Criar Invoice Simples (PDF)

```bash
# Instalar wkhtmltopdf para gerar PDFs
sudo apt install wkhtmltopdf -y

# Script para gerar invoice
cat > /opt/digiforge/generate_invoice.sh << 'EOF'
#!/bin/bash
CLIENT_NAME="$1"
CLIENT_EMAIL="$2"
PLAN="$3"
AMOUNT="$4"
INVOICE_NUM="INV-$(date +%Y%m%d%H%M%S)"
DATE=$(date +"%d/%m/%Y")

cat > /tmp/invoice.html << HTML
<!DOCTYPE html>
<html>
<head>
<style>
  body { font-family: Arial, sans-serif; padding: 40px; }
  .header { border-bottom: 2px solid #333; padding-bottom: 20px; margin-bottom: 30px; }
  .title { font-size: 28px; font-weight: bold; }
  .invoice-num { color: #666; }
  table { width: 100%; border-collapse: collapse; margin: 20px 0; }
  th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
  th { background: #f5f5f5; }
  .total { font-size: 20px; font-weight: bold; }
  .footer { margin-top: 40px; color: #666; font-size: 12px; }
</style>
</head>
<body>
<div class="header">
  <div class="title">DigiForge</div>
  <div class="invoice-num">Fatura: $INVOICE_NUM</div>
  <div>Data: $DATE</div>
</div>

<h3>Cliente</h3>
<p>
  <strong>$CLIENT_NAME</strong><br>
  $CLIENT_EMAIL
</p>

<table>
  <tr><th>Descrição</th><th>Quantidade</th><th>Preço</th></tr>
  <tr><td>DigiForge Plano ${PLAN^}</td><td>1 mês</td><td>€$AMOUNT</td></tr>
</table>

<p class="total">Total: €$AMOUNT</p>

<div class="footer">
  DigiForge - Plataforma de Produtos Digitais com IA<br>
  Esta fatura é um documento interno para controlo.
</div>
</body>
</html>
HTML

wkhtmltopdf /tmp/invoice.html "/opt/digiforge/invoices/${INVOICE_NUM}.pdf"
echo "Invoice created: /opt/digiforge/invoices/${INVOICE_NUM}.pdf"
EOF

chmod +x /opt/digiforge/generate_invoice.sh
mkdir -p /opt/digiforge/invoices
```

**Uso:**
```bash
./generate_invoice.sh "João Silva" "joao@exemplo.com" "pro" "29.99"
```

---

## 10. Checklist de Produção

Executa cada comando e verifica que passa:

```bash
#!/bin/bash
echo "=========================================="
echo "DigiForge Production Checklist"
echo "=========================================="

DOMAIN="digiforge.teudominio.com"  # AJUSTAR!
API_DOMAIN="api.digiforge.teudominio.com"  # AJUSTAR!

# 1. Docker containers running
echo -n "1. Docker containers: "
if docker ps | grep -q "digiforge-caddy" && \
   docker ps | grep -q "digiforge-backend" && \
   docker ps | grep -q "digiforge-frontend" && \
   docker ps | grep -q "digiforge-mongodb"; then
    echo "✅ PASS"
else
    echo "❌ FAIL"
fi

# 2. Firewall configured
echo -n "2. Firewall: "
if sudo ufw status | grep -q "80/tcp.*ALLOW"; then
    echo "✅ PASS"
else
    echo "❌ FAIL"
fi

# 3. SSL certificate
echo -n "3. SSL certificate: "
if curl -sI "https://$DOMAIN" 2>/dev/null | grep -q "200\|301\|302"; then
    echo "✅ PASS"
else
    echo "❌ FAIL"
fi

# 4. API responding
echo -n "4. API status: "
API_STATUS=$(curl -s "https://$API_DOMAIN/api/status" 2>/dev/null)
if echo "$API_STATUS" | grep -q "database_connected.*true"; then
    echo "✅ PASS"
else
    echo "❌ FAIL"
fi

# 5. LLM provider configured
echo -n "5. LLM provider: "
LLM=$(echo "$API_STATUS" | grep -o '"llm_provider":"[^"]*"' | cut -d'"' -f4)
echo "✅ $LLM"

# 6. Frontend loading
echo -n "6. Frontend: "
if curl -sI "https://$DOMAIN" 2>/dev/null | grep -q "200"; then
    echo "✅ PASS"
else
    echo "❌ FAIL"
fi

# 7. Admin user exists
echo -n "7. Admin user: "
ADMIN_COUNT=$(docker exec digiforge-mongodb mongosh digiforge --quiet --eval "db.users.countDocuments({is_admin: true})")
if [ "$ADMIN_COUNT" -gt 0 ]; then
    echo "✅ PASS ($ADMIN_COUNT admin(s))"
else
    echo "❌ FAIL (no admin users)"
fi

# 8. Backups configured
echo -n "8. Backups cron: "
if crontab -l 2>/dev/null | grep -q "backup.sh"; then
    echo "✅ PASS"
else
    echo "⚠️ NOT CONFIGURED"
fi

# 9. Disk space
echo -n "9. Disk space: "
DISK_USE=$(df -h / | tail -1 | awk '{print $5}' | sed 's/%//')
if [ "$DISK_USE" -lt 80 ]; then
    echo "✅ PASS (${DISK_USE}% used)"
else
    echo "⚠️ WARNING (${DISK_USE}% used)"
fi

# 10. Memory
echo -n "10. Memory: "
MEM_FREE=$(free -m | awk '/^Mem:/ {print $7}')
if [ "$MEM_FREE" -gt 500 ]; then
    echo "✅ PASS (${MEM_FREE}MB available)"
else
    echo "⚠️ WARNING (${MEM_FREE}MB available)"
fi

echo ""
echo "=========================================="
echo "Checklist complete!"
echo "=========================================="
```

Guarda e executa:
```bash
cat > /opt/digiforge/production_checklist.sh << 'CHECKLIST'
# (colar o script acima)
CHECKLIST

chmod +x /opt/digiforge/production_checklist.sh
./production_checklist.sh
```

---

## 11. Troubleshooting

### Problema: Certificado SSL não funciona

```bash
# Ver logs do Caddy
docker logs digiforge-caddy

# Verificar se porta 80 está acessível externamente
# Usa: https://canyouseeme.org (porta 80)

# Reiniciar Caddy
docker restart digiforge-caddy
```

### Problema: API não responde

```bash
# Ver logs do backend
docker logs digiforge-backend --tail=100

# Reiniciar backend
docker restart digiforge-backend

# Verificar MongoDB
docker exec digiforge-mongodb mongosh --eval "db.runCommand({ping:1})"
```

### Problema: Frontend não carrega

```bash
# Ver logs do frontend
docker logs digiforge-frontend

# Rebuild frontend (se alteraste REACT_APP_BACKEND_URL)
docker compose -f docker-compose.prod.yml build frontend
docker compose -f docker-compose.prod.yml up -d frontend
```

### Problema: Sem espaço em disco

```bash
# Limpar imagens Docker não usadas
docker system prune -a

# Limpar backups antigos
find /opt/backups/digiforge -mtime +30 -delete
```

---

## 12. Resumo de Comandos Úteis

```bash
# Diretório do projeto
cd /opt/digiforge

# Iniciar tudo
docker compose -f docker-compose.prod.yml up -d

# Parar tudo
docker compose -f docker-compose.prod.yml down

# Reiniciar serviço específico
docker compose -f docker-compose.prod.yml restart backend

# Ver logs
docker compose -f docker-compose.prod.yml logs -f

# Backup manual
./backup.sh

# Health check
./healthcheck.sh

# Gestão de clientes
./manage_customer.sh info cliente@exemplo.com
./manage_customer.sh set-plan cliente@exemplo.com pro
./manage_customer.sh add-credits cliente@exemplo.com 100

# Atualizar aplicação
git pull && docker compose -f docker-compose.prod.yml build && docker compose -f docker-compose.prod.yml up -d

# Checklist de produção
./production_checklist.sh
```

---

## 13. Custos Reais

| Item | Custo Mensal |
|------|--------------|
| Servidor (casa) | €0 (eletricidade ~€2-5) |
| Domínio | ~€1 (~€10-12/ano) |
| DuckDNS | €0 |
| Let's Encrypt SSL | €0 |
| OpenAI (opcional) | €0-20 (conforme uso) |
| Stripe (opcional) | 1.4% + €0.25/transação |
| **TOTAL (modo mock)** | **~€1-5/mês** |
| **TOTAL (com OpenAI)** | **~€5-25/mês** |

---

**Guia completo. Pronto para produção.**
