# NOXLOOP - Product Requirements Document

**Version:** 2.1.0  
**Status:** Production Ready  
**Last Updated:** February 2026

---

## Overview

NOXLOOP is a 100% self-hosted SaaS platform for AI-powered digital product creation and monetization. Users can generate eBooks, guides, courses and templates with AI, publish them with landing pages, and sell via Stripe integration.

---

## Core Features (Implemented)

### Authentication
- [x] Email/password registration and login
- [x] JWT token-based sessions (30 days)
- [x] Google OAuth (optional)
- [x] Admin role system (is_admin flag)

### Multi-Tenancy
- [x] Workspaces with owner/admin/member roles
- [x] Per-workspace credits and plans
- [x] Member invitations

### AI Product Generation
- [x] 4 product types: eBook, Guide, Course, Template
- [x] Configurable tone and language (default: PT-PT)
- [x] Mock provider (free, no API needed)
- [x] OpenAI provider (optional)
- [x] Credits consumption (5 credits per generation)

### Product Publishing
- [x] Draft/Published status workflow
- [x] Auto-generated SEO slugs
- [x] Public product pages (/p/{slug})
- [x] Landing page generation with AI

### Media Studio (Admin)
- [x] Media asset upload (images, videos, PDFs)
- [x] Associate media with products (media_asset_ids)
- [x] Hero image display on public pages
- [x] Promo Pack export (JSON with product + assets)

### Billing & Payments
- [x] Credit-based system
- [x] 4 plans: Free (10), Starter (50), Pro (200), Enterprise (1000 credits/month)
- [x] Stripe checkout integration
- [x] Stripe webhooks (checkout.session.completed, invoice.payment_succeeded)
- [x] Purchase records and entitlements

### Admin Backoffice
- [x] System statistics dashboard
- [x] User management
- [x] Template management
- [x] Plan configuration
- [x] Media Assets management
- [x] Promo Packs generation

### Security
- [x] Admin route protection (backend + frontend)
- [x] Role-based access control
- [x] Webhook idempotency (processed_events collection)
- [x] Health check endpoint (/api/health)
- [x] Environment variable validation on startup

---

## Technical Stack

| Component | Technology |
|-----------|------------|
| Backend | FastAPI (Python 3.11) |
| Frontend | React 18 + TailwindCSS + shadcn/ui |
| Database | MongoDB 7.0 |
| Payments | Stripe API |
| AI | OpenAI API (optional) |
| Containerization | Docker + Docker Compose |

---

## API Endpoints (Key)

| Method | Endpoint | Auth | Purpose |
|--------|----------|------|---------|
| GET | /api/health | No | Health check |
| POST | /api/auth/register | No | User registration |
| POST | /api/auth/login | No | User login |
| GET | /api/auth/me | Yes | Current user profile |
| POST | /api/products/generate | Yes | Generate product (5 credits) |
| GET | /api/products/{id} | Yes | Get product details |
| PUT | /api/products/{id} | Yes | Update product (inc. media_asset_ids) |
| GET | /api/public/products | No | List published products |
| GET | /api/public/product/{id} | No | Get public product |
| GET | /api/media/{asset_id} | No | Serve media file (public) |
| POST | /api/admin/media/upload | Admin | Upload media asset |
| GET | /api/admin/media | Admin | List media assets |
| DELETE | /api/admin/media/{id} | Admin | Delete media asset |
| GET | /api/admin/stats | Admin | Admin statistics |

---

## Database Collections

- `users` - User accounts (email, password_hash, is_admin)
- `workspaces` - Tenant workspaces (credits, plan)
- `workspace_members` - User-workspace relationships
- `products` - Generated products (status, slug, media_asset_ids)
- `purchases` - Product purchase records
- `media_assets` - Uploaded media files metadata
- `processed_events` - Stripe webhook idempotency
- `templates` - Admin prompt templates
- `plans` - Plan configurations

---

## Completed Work (This Session)

### Feb 2026 - Admin Media Studio
- [x] Fixed AdminPage.jsx tabs syntax (Media + Promo tabs)
- [x] Added GET /api/media/{asset_id} public endpoint
- [x] Added legacy GET/PUT /api/products/{product_id} endpoints
- [x] Updated ProductDetailPage with Media tab for admins
- [x] Updated PublicProductPage to show hero image from media_asset_ids
- [x] Fixed MediaAssetResponse schema (removed invalid fields)
- [x] All backend/frontend tests passing (100%)

---

## Backlog

### P0 (Critical for Commercial Flow)
- [ ] Complete Stripe checkout end-to-end test
- [ ] Implement credit renewal via invoice.payment_succeeded webhook
- [ ] Display user credits in dashboard header

### P1 (Important)
- [ ] Transactional emails (SMTP configuration)
- [ ] PDF export for products
- [ ] WYSIWYG content editor

### P2 (Future)
- [ ] Discount coupons
- [ ] Affiliate program
- [ ] A/B testing for landing pages
- [ ] Campaign history in UI

---

## Documentation

- `/app/README.md` - Project overview and quick start
- `/app/PRODUCTION_DEPLOYMENT_GUIDE.md` - Complete deployment guide
- `/app/SMOKE_TEST.md` - End-to-end QA test guide
- `/app/.env.example` - Environment variables template

---

## Test Credentials

| User | Email | Password | Role |
|------|-------|----------|------|
| Admin | test_admin@noxloop.com | admin123456 | is_admin: true |

---

## Changelog

### v2.1.0 (Feb 2026)
- Admin Media Studio complete
- Media assets can be associated with products
- Hero images on public product pages
- Promo Packs export functionality
- Fixed MediaAssetResponse schema
- All tests passing (100%)

### v2.0.0 (Feb 2026)
- Rebranding from DigiForge to NOXLOOP
- Public product pages with slugs
- Stripe integration for purchases
- Admin/User role separation
- Health check endpoint
- Environment validation

### v1.0.0 (Feb 2026)
- Initial MVP with product generation
