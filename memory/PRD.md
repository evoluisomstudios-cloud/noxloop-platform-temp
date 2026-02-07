# DigiForge - Product Requirements Document

**Version:** 2.0.0  
**Status:** Production Ready  
**Last Updated:** February 2026

---

## Overview

DigiForge is a 100% self-hosted SaaS platform for AI-powered digital product and marketing campaign generation. Runs entirely on your own infrastructure with €0 monthly costs.

---

## Core Features (Implemented)

### Authentication
- [x] Email/password registration and login
- [x] JWT token-based sessions (7 days)
- [x] Google OAuth (optional)
- [x] Admin role system

### Multi-Tenancy
- [x] Workspaces with owner/admin/member roles
- [x] Per-workspace credits and plans
- [x] Member invitations

### AI Product Generation
- [x] 4 product types: eBook, Guide, Course, Template
- [x] Configurable tone and language
- [x] Mock provider (free, no API needed)
- [x] OpenAI provider (optional)
- [x] Local LLM provider (optional)

### Campaign Builder
- [x] Landing page copy generation
- [x] Ad variations (5 per campaign)
- [x] Email sequence (5 emails)
- [x] Creative ideas
- [x] Publication checklist
- [x] ZIP export

### Admin Backoffice
- [x] System statistics
- [x] User management
- [x] Template management
- [x] Plan configuration

### Billing
- [x] Credit-based system
- [x] 4 plans: Free (10), Starter (50), Pro (200), Enterprise (1000)
- [x] Manual credit management via scripts
- [x] Stripe integration (optional)

---

## Technical Stack

| Component | Technology |
|-----------|------------|
| Backend | FastAPI (Python 3.11) |
| Frontend | React 18 + TailwindCSS |
| Database | MongoDB 6.0 |
| Containerization | Docker + Docker Compose |
| Reverse Proxy | Caddy (auto-SSL) or Nginx + Certbot |

---

## Deployment Options

| File | Use Case |
|------|----------|
| `docker-compose.yml` | Development |
| `docker-compose.prod.yml` | Production with Caddy |
| `docker-compose.nginx.yml` | Production with external Nginx |

---

## API Endpoints

| Method | Endpoint | Auth | Credits |
|--------|----------|------|---------|
| GET | /api/status | No | 0 |
| POST | /api/auth/register | No | 0 |
| POST | /api/auth/login | No | 0 |
| GET | /api/auth/me | Yes | 0 |
| POST | /api/products/generate | Yes | 1 |
| POST | /api/workspaces/{id}/campaigns/generate | Yes | 3 |
| GET | /api/admin/stats | Admin | 0 |

---

## File Structure

```
digiforge-saas/
├── backend/
│   ├── server.py
│   ├── services/
│   ├── models/
│   └── Dockerfile
├── frontend/
│   ├── src/
│   └── Dockerfile
├── scripts/
│   ├── backup.sh
│   ├── healthcheck.sh
│   └── manage_customer.sh
├── docs/
│   ├── SELF_HOSTING_GUIDE.md
│   └── PRODUCTION_DEPLOYMENT_GUIDE.md
├── docker-compose.yml
├── docker-compose.prod.yml
├── docker-compose.nginx.yml
├── Caddyfile
└── .env.example
```

---

## Customer Lifecycle

1. **Registration** → User creates account → Gets Free plan (10 credits)
2. **Usage** → User generates products/campaigns → Credits deducted
3. **Upgrade** → Admin sets plan via `manage_customer.sh set-plan EMAIL pro`
4. **Renewal** → Admin adds credits via `manage_customer.sh add-credits EMAIL 200`

---

## Backlog

### P1 (Next)
- [ ] PDF export for products
- [ ] WYSIWYG content editor
- [ ] Campaign history in UI

### P2 (Future)
- [ ] Discount coupons
- [ ] Affiliate program
- [ ] Email marketing integration
- [ ] A/B testing

---

## Changelog

### v2.0.0 (Feb 2026)
- 100% self-hosted capability
- LLM provider abstraction (mock/openai/local)
- Campaign Builder with full asset generation
- Admin Backoffice
- Multi-tenant workspaces
- Complete deployment documentation

### v1.0.0 (Feb 2026)
- Initial MVP with product generation
