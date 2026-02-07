# DigiForge - Plataforma de Produtos Digitais com IA

**100% Self-Hosted** | FastAPI + React + MongoDB | Docker Ready

---

## Quick Start (Desenvolvimento)

```bash
# Clonar repositório
git clone https://github.com/daremoservice/digiforge-saas.git
cd digiforge-saas

# Copiar configuração
cp backend/.env.example backend/.env

# Iniciar com Docker Compose
docker compose up -d

# Verificar status
curl http://localhost:8001/api/status
```

**URLs:**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8001/api
- API Status: http://localhost:8001/api/status

---

## Arquitetura

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│    Frontend     │────▶│     Backend     │────▶│    MongoDB      │
│  React :3000    │     │  FastAPI :8001  │     │     :27017      │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

---

## Portas e Serviços

| Serviço | Porta | Descrição |
|---------|-------|-----------|
| Frontend | 3000 | React SPA |
| Backend | 8001 | FastAPI REST API |
| MongoDB | 27017 | Base de dados |

---

## Docker Compose

```bash
# Iniciar todos os serviços
docker compose up -d

# Ver logs
docker compose logs -f

# Ver logs de um serviço
docker compose logs -f backend

# Parar tudo
docker compose down

# Rebuild após alterações
docker compose build
docker compose up -d

# Reiniciar serviço específico
docker compose restart backend
```

---

## Variáveis de Ambiente

Ficheiro: `backend/.env`

```env
# Database
MONGO_URL=mongodb://localhost:27017
DB_NAME=digiforge

# Security
JWT_SECRET_KEY=your-secret-key

# LLM Provider: mock | openai | local_llm
LLM_PROVIDER=mock
OPENAI_API_KEY=

# Optional
STRIPE_ENABLED=false
RAG_ENABLED=false
```

Ver `backend/.env.example` para todas as opções.

---

## Endpoints Principais

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/api/status` | Health check |
| POST | `/api/auth/register` | Registar utilizador |
| POST | `/api/auth/login` | Login |
| GET | `/api/auth/me` | Perfil do utilizador |
| GET | `/api/workspaces` | Listar workspaces |
| POST | `/api/products/generate` | Gerar produto |
| POST | `/api/workspaces/{id}/campaigns/generate` | Gerar campanha |
| GET | `/api/admin/stats` | Stats (admin) |

---

## Troubleshooting

### Container não inicia
```bash
docker compose logs backend
# Verificar se .env existe
cat backend/.env
```

### MongoDB não conecta
```bash
docker compose logs mongodb
# Verificar se o container está a correr
docker ps | grep mongodb
```

### Frontend não carrega
```bash
# Verificar se REACT_APP_BACKEND_URL está correto
cat frontend/.env
# Rebuild se necessário
docker compose build frontend
```

### API retorna 500
```bash
# Ver logs detalhados
docker compose logs -f backend 2>&1 | grep -i error
```

### Reset completo
```bash
docker compose down -v
docker compose up -d
```

---

## Estrutura do Projeto

```
digiforge-saas/
├── backend/
│   ├── server.py           # API principal
│   ├── services/           # Lógica de negócio
│   ├── models/             # Schemas Pydantic
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── pages/          # Páginas React
│   │   └── components/     # Componentes UI
│   ├── Dockerfile
│   └── package.json
├── scripts/
│   ├── backup.sh           # Script de backup
│   ├── healthcheck.sh      # Health check
│   └── manage_customer.sh  # Gestão de clientes
├── docs/
│   ├── SELF_HOSTING_GUIDE.md
│   └── PRODUCTION_DEPLOYMENT_GUIDE.md
├── docker-compose.yml      # Dev
├── docker-compose.prod.yml # Produção
└── Caddyfile               # Reverse proxy config
```

---

## Deploy para Produção

Ver documentação completa em:
- [SELF_HOSTING_GUIDE.md](docs/SELF_HOSTING_GUIDE.md) - Guia completo
- [PRODUCTION_DEPLOYMENT_GUIDE.md](docs/PRODUCTION_DEPLOYMENT_GUIDE.md) - Deploy detalhado

**Quick production start:**
```bash
cp .env.example .env
# Editar .env com domínio e JWT_SECRET_KEY
docker compose -f docker-compose.prod.yml up -d
```

---

## Licença

MIT License

---

## Suporte

- Issues: GitHub Issues
- Docs: `/docs/`
