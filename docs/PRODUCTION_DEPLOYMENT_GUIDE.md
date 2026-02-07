# DigiForge - Production Deployment Guide

Guia completo para deploy em produção num servidor Ubuntu com €0 de custos mensais.

---

## 1. Setup do Domínio e DNS

### Opção A: Cloudflare (se tens domínio)

1. Acede a [dash.cloudflare.com](https://dash.cloudflare.com)
2. Seleciona o teu domínio
3. Vai a **DNS** → **Records**
4. Adiciona:

| Tipo | Nome | Conteúdo | Proxy Status | TTL |
|------|------|----------|--------------|-----|
| A | digiforge | `TEU_IP_PUBLICO` | DNS only (cinzento) | Auto |
| A | api.digiforge | `TEU_IP_PUBLICO` | DNS only (cinzento) | Auto |

**Obter IP público:**
```bash
curl -s ifconfig.me
```

### Opção B: DuckDNS (grátis, sem domínio)

1. Vai a [duckdns.org](https://www.duckdns.org)
2. Login com Google/GitHub
3. Cria subdomínio: `meuprojeto` → `meuprojeto.duckdns.org`
4. Guarda o **token**

```bash
# Script de atualização de IP
mkdir -p /opt/duckdns
cat > /opt/duckdns/duck.sh << 'EOF'
#!/bin/bash
DOMAIN="meuprojeto"
TOKEN="TEU_TOKEN_AQUI"
curl -s "https://www.duckdns.org/update?domains=$DOMAIN&token=$TOKEN&ip="
EOF
chmod +x /opt/duckdns/duck.sh

# Cron para atualizar a cada 5 minutos
(crontab -l 2>/dev/null; echo "*/5 * * * * /opt/duckdns/duck.sh >/dev/null 2>&1") | crontab -
```

---

## 2. Instalação do Servidor (Ubuntu 22.04)

### 2.1 Atualizar Sistema

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y curl git ufw fail2ban nginx certbot python3-certbot-nginx
```

### 2.2 Instalar Docker

```bash
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER
sudo apt install -y docker-compose-plugin

# Logout e login para aplicar grupo
exit
# (fazer login novamente)

# Verificar
docker --version
docker compose version
```

### 2.3 Configurar Firewall

```bash
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
sudo ufw status
```

### 2.4 Configurar Fail2ban

```bash
sudo tee /etc/fail2ban/jail.local << 'EOF'
[sshd]
enabled = true
port = 22
maxretry = 3
bantime = 3600
EOF

sudo systemctl restart fail2ban
sudo systemctl enable fail2ban
```

---

## 3. Deploy da Aplicação

### 3.1 Clonar Repositório

```bash
sudo mkdir -p /opt/digiforge
sudo chown $USER:$USER /opt/digiforge
cd /opt/digiforge
git clone https://github.com/daremoservice/digiforge-saas.git .
```

### 3.2 Configurar Variáveis de Ambiente

```bash
# Gerar JWT secret
JWT_SECRET=$(openssl rand -hex 32)
echo "JWT Secret: $JWT_SECRET"

# Criar .env principal
cat > /opt/digiforge/.env << EOF
# === DOMÍNIO ===
DOMAIN=digiforge.teudominio.com
API_DOMAIN=api.digiforge.teudominio.com

# === SEGURANÇA ===
JWT_SECRET_KEY=$JWT_SECRET

# === ADMIN ===
ADMIN_EMAIL=admin@teudominio.com
ADMIN_PASSWORD=SenhaSegura123!

# === LLM (mock = sem custos) ===
LLM_PROVIDER=mock
OPENAI_API_KEY=
OPENAI_MODEL=gpt-4o

# === INTEGRAÇÕES (todas desativadas) ===
STRIPE_ENABLED=false
STRIPE_API_KEY=
RAG_ENABLED=false
N8N_WEBHOOK_ENABLED=false
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
EOF

# Criar backend/.env
cat > /opt/digiforge/backend/.env << 'EOF'
MONGO_URL=mongodb://mongodb:27017
DB_NAME=digiforge
CORS_ORIGINS=*
EOF
```

### 3.3 Build e Iniciar

```bash
cd /opt/digiforge

# Build
docker compose build

# Iniciar
docker compose up -d

# Verificar
docker compose ps
curl http://localhost:8001/api/status
```

---

## 4. Configurar SSL com Nginx + Certbot

### 4.1 Configurar Nginx

```bash
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
    }
}

# API
server {
    listen 80;
    server_name api.digiforge.teudominio.com;

    client_max_body_size 50M;

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

# Ativar
sudo ln -sf /etc/nginx/sites-available/digiforge /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx
```

### 4.2 Obter Certificado SSL

```bash
# Substituir pelos teus domínios e email
sudo certbot --nginx \
  -d digiforge.teudominio.com \
  -d api.digiforge.teudominio.com \
  --non-interactive \
  --agree-tos \
  -m teu@email.com

# Verificar renovação automática
sudo systemctl status certbot.timer
```

---

## 5. .env.example Completo

Ficheiro de referência com todas as variáveis disponíveis:

```env
# =============================================
# DigiForge Production Environment
# =============================================

# === DOMÍNIO (obrigatório) ===
DOMAIN=digiforge.exemplo.com
API_DOMAIN=api.digiforge.exemplo.com

# === SEGURANÇA (obrigatório) ===
# Gerar: openssl rand -hex 32
JWT_SECRET_KEY=

# === ADMIN (obrigatório) ===
ADMIN_EMAIL=admin@exemplo.com
ADMIN_PASSWORD=

# === LLM PROVIDER ===
# Opções: mock (grátis), openai, local_llm
LLM_PROVIDER=mock

# Se LLM_PROVIDER=openai:
OPENAI_API_KEY=
OPENAI_MODEL=gpt-4o

# Se LLM_PROVIDER=local_llm:
LOCAL_LLM_BASE_URL=http://192.168.1.100:5002
LOCAL_LLM_API_KEY=not-needed
LOCAL_LLM_MODEL=llama3

# === STRIPE (opcional) ===
# Taxa: 1.4% + €0.25/transação
STRIPE_ENABLED=false
STRIPE_API_KEY=
STRIPE_WEBHOOK_SECRET=

# === RAG (opcional) ===
RAG_ENABLED=false
RAG_BASE_URL=http://192.168.1.100:8811
RAG_TOP_K=5

# === WEBHOOKS N8N (opcional) ===
N8N_WEBHOOK_ENABLED=false
N8N_WEBHOOK_URL=

# === GOOGLE OAUTH (opcional) ===
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
```

---

## 6. First Paying Customer Setup

### 6.1 Criar Utilizador Admin

```bash
# Via API
API="https://api.digiforge.teudominio.com"

curl -X POST "$API/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@teudominio.com",
    "password": "SenhaSegura123!",
    "name": "Administrador"
  }'
```

### 6.2 Promover a Admin

```bash
docker exec -it digiforge-mongodb mongosh digiforge --eval "
  db.users.updateOne(
    {email: 'admin@teudominio.com'},
    {\$set: {is_admin: true}}
  )
"
```

### 6.3 Registar Primeiro Cliente

```bash
# Cliente regista-se via frontend ou API
curl -X POST "$API/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "cliente@exemplo.com",
    "password": "ClientePass123!",
    "name": "João Silva"
  }'
```

### 6.4 Ativar Plano Pago para Cliente

**Planos disponíveis:**
| Plano | Créditos | Preço Sugerido |
|-------|----------|----------------|
| free | 10 | €0 |
| starter | 50 | €9.99/mês |
| pro | 200 | €29.99/mês |
| enterprise | 1000 | €99.99/mês |

```bash
# Definir plano Pro para cliente
docker exec -it digiforge-mongodb mongosh digiforge --eval "
  var user = db.users.findOne({email: 'cliente@exemplo.com'});
  var membership = db.workspace_members.findOne({user_id: user.user_id});
  db.workspaces.updateOne(
    {workspace_id: membership.workspace_id},
    {\$set: {plan: 'pro', credits: 200}}
  );
  print('Plano Pro ativado para cliente@exemplo.com');
"
```

### 6.5 Adicionar Créditos Manualmente

```bash
# Adicionar 100 créditos
docker exec -it digiforge-mongodb mongosh digiforge --eval "
  var user = db.users.findOne({email: 'cliente@exemplo.com'});
  var membership = db.workspace_members.findOne({user_id: user.user_id});
  db.workspaces.updateOne(
    {workspace_id: membership.workspace_id},
    {\$inc: {credits: 100}}
  );
  print('100 créditos adicionados');
"
```

### 6.6 Script de Gestão de Clientes

```bash
# Usar script incluído
cd /opt/digiforge

# Ver info de cliente
./scripts/manage_customer.sh info cliente@exemplo.com

# Definir plano
./scripts/manage_customer.sh set-plan cliente@exemplo.com pro

# Adicionar créditos
./scripts/manage_customer.sh add-credits cliente@exemplo.com 50

# Listar todos os utilizadores
./scripts/manage_customer.sh list-users
```

---

## 7. Workflow de Pagamento Manual (Sem Stripe)

1. **Cliente contacta-te** pedindo upgrade
2. **Envias link de pagamento:**
   - MBWay: teu número
   - PayPal: paypal.me/teuusername
   - IBAN: para transferência
3. **Cliente paga e envia comprovativo**
4. **Tu ativas o plano:**
   ```bash
   ./scripts/manage_customer.sh set-plan cliente@email.com pro
   ```
5. **Confirmas por email ao cliente**

---

## 8. Checklist de Onboarding

### Para Ti (Admin)

- [ ] Servidor Ubuntu instalado
- [ ] Docker + Compose funcionando
- [ ] Domínio configurado (DNS)
- [ ] SSL ativo (HTTPS)
- [ ] UFW e Fail2ban ativos
- [ ] Backups automáticos configurados
- [ ] Utilizador admin criado e promovido
- [ ] API respondendo: `curl https://api.teudominio.com/api/status`
- [ ] Frontend carregando: `curl -I https://teudominio.com`

### Para Cliente Novo

- [ ] Conta criada (registo)
- [ ] Plano definido (via script)
- [ ] Créditos atribuídos
- [ ] Email de boas-vindas enviado
- [ ] Primeiro produto/campanha gerado (teste)

---

## 9. Comandos de Verificação

```bash
# Status dos containers
docker compose ps

# Health check API
curl https://api.teudominio.com/api/status | jq

# Ver logs
docker compose logs -f backend

# Estatísticas de uso
docker stats --no-stream

# Espaço em disco
df -h

# Verificar SSL
echo | openssl s_client -connect teudominio.com:443 2>/dev/null | openssl x509 -noout -dates

# Verificar Nginx
sudo nginx -t
sudo systemctl status nginx

# Verificar certificado
sudo certbot certificates
```

---

## 10. Troubleshooting Rápido

| Problema | Solução |
|----------|---------|
| SSL não funciona | Verificar DNS propagado, porta 80 aberta, proxy Cloudflare desativado |
| API 502 | `docker compose restart backend` |
| Frontend não carrega | `docker compose restart frontend` |
| MongoDB erro | `docker compose logs mongodb` |
| Sem espaço | `docker system prune -a` |

---

## 11. Manutenção

### Atualizar

```bash
cd /opt/digiforge
./scripts/backup.sh
git pull origin main
docker compose build
docker compose up -d
```

### Backup Manual

```bash
./scripts/backup.sh
```

### Ver Logs

```bash
docker compose logs -f --tail=100
```

---

**Deploy completo. Pronto para produção.**
