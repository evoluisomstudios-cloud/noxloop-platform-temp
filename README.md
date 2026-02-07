# NOXLOOP SaaS - 100% Self-Hosted AI Digital Product Platform

<div align="center">
  <h3>🚀 Plataforma SaaS completa para criação e venda de produtos digitais com IA</h3>
  <p>FastAPI • React • MongoDB • Stripe • OpenAI</p>
</div>

---

## ✨ Funcionalidades

### 🎯 Produtos Digitais
- ✅ Geração de produtos com IA (eBooks, guias, cursos, templates)
- ✅ Sistema de créditos (5 créditos por geração)
- ✅ Publicação de produtos (draft → published)
- ✅ Páginas públicas de venda
- ✅ Compra via Stripe checkout
- ✅ Entrega automática após pagamento

### 💳 Monetização
- ✅ 3 planos: Starter (50), Pro (200), Enterprise (1000 créditos/mês)
- ✅ Pagamentos Stripe + PayPal
- ✅ Webhooks automáticos para renovação mensal
- ✅ Downgrade automático em cancelamento

### 📧 Emails Transacionais
- ✅ Boas-vindas
- ✅ Confirmação de compra
- ✅ Reset password
- ✅ Créditos baixos
- ✅ Cancelamento de assinatura

### 👥 Multi-tenancy
- ✅ Workspaces com membros (owner/admin/member)
- ✅ Roles e permissões
- ✅ Gestão de equipa

### 🔐 Autenticação
- ✅ Email/Password
- ✅ Google OAuth
- ✅ JWT tokens
- ✅ Password reset

### 📊 Analytics & Admin
- ✅ Dashboard com estatísticas
- ✅ Métricas de uso
- ✅ Histórico de pagamentos
- ✅ Logs de auditoria

---

## 🏗️ Arquitetura

```
noxloop-saas/
├── backend/              # FastAPI backend
│   ├── server.py         # Main API
│   ├── models/           # Pydantic schemas
│   ├── services/         # Business logic
│   │   ├── llm_service.py
│   │   ├── payment_service.py
│   │   ├── email_service.py
│   │   └── security_service.py
│   ├── Dockerfile
│   └── requirements.txt
│
├── frontend/             # React SPA
│   ├── src/
│   │   ├── pages/        # Route components
│   │   └── components/   # UI components
│   ├── Dockerfile
│   ├── nginx.conf
│   └── package.json
│
├── docker-compose.yml    # Full stack orchestration
├── scripts/              # Maintenance scripts
│   ├── backup-mongo.sh
│   └── restore-mongo.sh
└── docs/                 # Documentation
```

---

## 🚀 Quick Start (Docker Compose)

### Prerequisites
- Docker 20.10+
- Docker Compose 2.0+
- Domain with DNS configured
- Stripe account
- OpenAI API key

### 1. Clone & Configure

```bash
git clone https://github.com/daremoservice/digiforge-saas.git noxloop
cd noxloop

# Copy environment template
cp .env.example .env

# Edit with your values
nano .env
```

### 2. Deploy

```bash
# Start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

### 3. Access

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8001/api
- **MongoDB**: localhost:27017

---

## 🔧 Configuration

### Environment Variables

```env
# MongoDB
MONGO_ROOT_USER=admin
MONGO_ROOT_PASSWORD=your-secure-password

# Backend
JWT_SECRET_KEY=random-64-char-string
CORS_ORIGINS=https://noxloop.pt

# Email (SMTP)
SMTP_ENABLED=true
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# Stripe
STRIPE_ENABLED=true
STRIPE_API_KEY=sk_live_xxxxx
STRIPE_WEBHOOK_SECRET=whsec_xxxxx

# OpenAI
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-xxxxx

# URLs
APP_URL=https://noxloop.pt
BACKEND_URL=https://noxloop.pt/api
```

### Stripe Webhooks

Configure webhook endpoint:
- URL: `https://noxloop.pt/api/billing/webhook/stripe`
- Events:
  - `checkout.session.completed`
  - `invoice.payment_succeeded`
  - `customer.subscription.deleted`

---

## 📦 MongoDB Collections

```javascript
// Core collections
users                 // User accounts
workspaces            // Tenant workspaces
workspace_members     // Membership & roles
products              // Generated products
purchases             // Product purchases
campaigns             // Marketing campaigns

// Billing & Usage
payments              // Payment history
plans                 // Plan configurations
usage                 // Usage logs

// Auth & Security
password_resets       // Reset tokens
templates             // Product templates
```

---

## 🔌 API Endpoints

### Authentication
- `POST /api/auth/register`
- `POST /api/auth/login`
- `GET /api/auth/me`
- `POST /api/auth/forgot-password`
- `POST /api/auth/reset-password`

### Products
- `POST /api/workspaces/{id}/products/generate` (5 credits)
- `GET /api/workspaces/{id}/products`
- `PUT /api/workspaces/{id}/products/{pid}` (publish/edit)
- `GET /api/public/product/{pid}` (public view)

### Purchases
- `POST /api/products/{pid}/purchase` (create checkout)
- `GET /api/purchases/verify?session_id=xxx` (verify payment)
- `GET /api/purchases/my` (user purchases)

### Billing
- `GET /api/billing/plans`
- `POST /api/billing/checkout/stripe`
- `POST /api/billing/webhook/stripe` (Stripe webhooks)
- `GET /api/billing/history`

---

## 🔐 Security

- JWT authentication with 30-day expiry
- bcrypt password hashing
- Rate limiting on credit operations
- CORS protection
- Stripe webhook signature verification
- MongoDB auth
- Environment variable isolation

---

## 📊 Monitoring

### Health Checks

```bash
# Backend
curl https://noxloop.pt/api/status

# Frontend
curl https://noxloop.pt/health

# MongoDB
docker exec noxloop-mongodb mongosh --eval "db.adminCommand('ping')"
```

### Logs

```bash
# All services
docker-compose logs -f

# Backend only
docker-compose logs -f backend

# Last 100 lines
docker-compose logs --tail=100 backend
```

---

## 💾 Backup & Restore

### Automated Daily Backups

```bash
# Run backup script
./scripts/backup-mongo.sh

# Add to crontab for daily backups at 2 AM
0 2 * * * /app/scripts/backup-mongo.sh
```

### Manual Restore

```bash
./scripts/restore-mongo.sh backup_20250207.archive.gz
```

---

## 🔄 Updates

```bash
# Pull latest code
git pull origin main

# Rebuild and restart
docker-compose build
docker-compose up -d

# Check logs
docker-compose logs -f backend frontend
```

---

## 🎯 User Flow

1. **User registers** → Welcome email → 10 free credits
2. **Creates product** → AI generates content → Consumes 5 credits
3. **Publishes product** → Gets public URL
4. **Customer visits public page** → Clicks buy
5. **Stripe checkout** → Payment processed
6. **Webhook confirms** → Access granted → Confirmation email
7. **Monthly renewal** → Credits reset automatically

---

## 📈 Scaling

### Horizontal Scaling

```yaml
# docker-compose.yml
backend:
  deploy:
    replicas: 3
  command: ["uvicorn", "server:app", "--workers", "4"]
```

### MongoDB Indexes

```javascript
db.users.createIndex({"email": 1}, {unique: true})
db.workspaces.createIndex({"owner_id": 1})
db.products.createIndex({"workspace_id": 1, "is_published": 1})
db.purchases.createIndex({"user_id": 1, "status": 1})
```

---

## 🛠️ Tech Stack

**Backend:**
- FastAPI 0.115+
- Motor (async MongoDB)
- Pydantic v2
- JWT authentication
- Stripe SDK
- OpenAI SDK

**Frontend:**
- React 18
- React Router v6
- Tailwind CSS
- shadcn/ui components
- Axios

**Infrastructure:**
- Docker & Docker Compose
- MongoDB 7.0
- Nginx (reverse proxy)
- Let's Encrypt SSL

---

## 📝 License

© 2025 NOXLOOP. All rights reserved.

---

## 🤝 Support

- 📧 Email: support@noxloop.pt
- 📚 Docs: [PRODUCTION_DEPLOYMENT_GUIDE.md](./PRODUCTION_DEPLOYMENT_GUIDE.md)
- 🐛 Issues: GitHub Issues

---

## ✅ Production Checklist

- [ ] Configure domain DNS
- [ ] Generate SSL certificates
- [ ] Set strong passwords (MongoDB, JWT secret)
- [ ] Configure Stripe webhooks
- [ ] Configure SMTP for emails
- [ ] Add OpenAI API key
- [ ] Set up automated backups
- [ ] Configure monitoring/alerts
- [ ] Test payment flow end-to-end
- [ ] Enable rate limiting
- [ ] Review security settings

---

**Built with ❤️ for creators who want to monetize AI-generated digital products.**
