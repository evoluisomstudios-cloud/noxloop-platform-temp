# DigiForge - Documentação Técnica

## Índice
1. [Visão Geral](#visão-geral)
2. [Arquitetura](#arquitetura)
3. [Instalação](#instalação)
4. [Configuração](#configuração)
5. [API Reference](#api-reference)
6. [Deploy](#deploy)

---

## Visão Geral

DigiForge é uma plataforma SaaS para geração e venda de produtos digitais usando Inteligência Artificial. A aplicação permite:

- Criar eBooks, guias, cursos e templates automaticamente com IA
- Gerar landing pages de venda otimizadas
- Processar pagamentos via Stripe
- Entregar produtos automaticamente aos clientes
- Visualizar analytics em tempo real

## Arquitetura

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend                              │
│                    (React + Tailwind)                        │
│                         :3000                                │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                        Backend                               │
│                       (FastAPI)                              │
│                         :8001                                │
└──────┬──────────────────┬───────────────────┬───────────────┘
       │                  │                   │
       ▼                  ▼                   ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────────┐
│   MongoDB    │  │   OpenAI     │  │     Stripe       │
│  (Database)  │  │  (GPT-5.2)   │  │   (Payments)     │
└──────────────┘  └──────────────┘  └──────────────────┘
```

### Stack Tecnológico

| Componente | Tecnologia |
|------------|------------|
| Frontend | React 19, Tailwind CSS, Shadcn UI |
| Backend | FastAPI, Python 3.11 |
| Database | MongoDB |
| AI | OpenAI GPT-5.2 |
| Payments | Stripe |
| Auth | JWT + Google OAuth |

## Instalação

### Pré-requisitos
- Python 3.11+
- Node.js 18+
- MongoDB 6.0+
- Yarn

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Frontend

```bash
cd frontend
yarn install
```

## Configuração

### Backend (.env)

```env
MONGO_URL="mongodb://localhost:27017"
DB_NAME="digiforge"
CORS_ORIGINS="*"
STRIPE_API_KEY=sk_test_your_key
EMERGENT_LLM_KEY=your_llm_key
JWT_SECRET_KEY=your_secret_key
```

### Frontend (.env)

```env
REACT_APP_BACKEND_URL=http://localhost:8001
```

## API Reference

### Autenticação

#### POST /api/auth/register
Regista um novo utilizador.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "password123",
  "name": "John Doe"
}
```

**Response:**
```json
{
  "user_id": "user_abc123",
  "email": "user@example.com",
  "name": "John Doe",
  "plan": "free",
  "credits": 10,
  "token": "eyJhbG..."
}
```

#### POST /api/auth/login
Autentica um utilizador existente.

#### POST /api/auth/session
Troca session_id do Google OAuth por token de sessão.

#### GET /api/auth/me
Obtém dados do utilizador autenticado.

#### POST /api/auth/logout
Termina a sessão do utilizador.

### Produtos

#### POST /api/products/generate
Gera um novo produto com IA.

**Request:**
```json
{
  "title": "Guia de Marketing",
  "description": "Guia completo...",
  "product_type": "guide",
  "topic": "Marketing Digital",
  "target_audience": "Empreendedores",
  "tone": "professional",
  "language": "pt"
}
```

#### GET /api/products
Lista todos os produtos do utilizador.

#### GET /api/products/{product_id}
Obtém detalhes de um produto.

#### PUT /api/products/{product_id}
Atualiza um produto.

#### DELETE /api/products/{product_id}
Elimina um produto.

#### POST /api/products/{product_id}/landing-page
Gera landing page com IA.

### Pagamentos

#### POST /api/checkout/create
Cria sessão de checkout Stripe.

**Request:**
```json
{
  "product_id": "prod_abc123",
  "origin_url": "https://example.com",
  "customer_email": "customer@example.com"
}
```

#### GET /api/checkout/status/{session_id}
Obtém status do pagamento.

#### POST /api/billing/subscribe
Cria subscrição de plano.

#### GET /api/billing/plans
Lista planos disponíveis.

### Analytics

#### GET /api/analytics
Obtém métricas do utilizador.

**Response:**
```json
{
  "total_revenue": 1250.00,
  "total_sales": 47,
  "total_products": 5,
  "total_views": 2340,
  "recent_sales": [...],
  "sales_by_day": [...]
}
```

## Deploy

### Docker Compose

```yaml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8001:8001"
    environment:
      - MONGO_URL=mongodb://mongo:27017
      - DB_NAME=digiforge
    depends_on:
      - mongo

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      - REACT_APP_BACKEND_URL=http://backend:8001

  mongo:
    image: mongo:6.0
    volumes:
      - mongo_data:/data/db

volumes:
  mongo_data:
```

### Variáveis de Ambiente de Produção

| Variável | Descrição |
|----------|-----------|
| MONGO_URL | URL de conexão MongoDB |
| STRIPE_API_KEY | Chave API Stripe (sk_live_...) |
| EMERGENT_LLM_KEY | Chave Universal LLM |
| JWT_SECRET_KEY | Chave secreta para JWT |

### Checklist de Deploy

- [ ] Configurar MongoDB com autenticação
- [ ] Usar HTTPS em produção
- [ ] Configurar CORS corretamente
- [ ] Usar chaves Stripe de produção
- [ ] Configurar backups de MongoDB
- [ ] Monitorizar logs e erros

---

## Suporte

Para questões técnicas, consulte a documentação ou abra uma issue no repositório.
