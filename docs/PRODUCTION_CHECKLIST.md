# DigiForge - Production Deployment Checklist

## ✅ Final Production Checklist

### 1. Security Configuration
```bash
# Generate secure JWT secret
openssl rand -hex 32
# Copy output to JWT_SECRET_KEY in .env
```

- [ ] JWT_SECRET_KEY is unique (not default)
- [ ] ADMIN_PASSWORD is strong (min 12 chars)
- [ ] RATE_LIMIT_ENABLED=true
- [ ] SSL/HTTPS enabled
- [ ] Firewall configured (UFW)

### 2. Payment Setup

#### Stripe (Card Payments)
1. Create account at https://stripe.com
2. Get API keys from Dashboard → Developers → API Keys
3. Configure webhook at Dashboard → Developers → Webhooks
   - Endpoint URL: `https://api.yourdomain.com/api/billing/webhook/stripe`
   - Events: `checkout.session.completed`

```bash
# .env configuration
STRIPE_ENABLED=true
STRIPE_API_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
```

#### PayPal (Alternative Payments)
1. Create Business account at https://paypal.com/business
2. Go to https://developer.paypal.com/dashboard
3. Create App → Get Client ID and Secret

```bash
# .env configuration
PAYPAL_ENABLED=true
PAYPAL_CLIENT_ID=...
PAYPAL_CLIENT_SECRET=...
PAYPAL_MODE=live  # Change from 'sandbox' to 'live'
```

### 3. Email Configuration

#### Gmail (Simple Setup)
1. Enable 2FA on Gmail account
2. Generate App Password: Google Account → Security → App Passwords
3. Use app password as SMTP_PASSWORD

```bash
EMAIL_ENABLED=true
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-16-char-app-password
SMTP_FROM_EMAIL=noreply@yourdomain.com
SMTP_FROM_NAME=DigiForge
```

#### SendGrid (Professional)
```bash
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USER=apikey
SMTP_PASSWORD=SG.your-api-key
```

### 4. Deployment Commands

```bash
# Production with Nginx (recommended)
cd /opt/digiforge
docker compose -f docker-compose.nginx.yml build
docker compose -f docker-compose.nginx.yml up -d

# Production with Caddy (includes SSL)
docker compose -f docker-compose.prod.yml build
docker compose -f docker-compose.prod.yml up -d

# Verify deployment
docker compose ps
curl https://api.yourdomain.com/api/status
```

### 5. Admin Bootstrap

```bash
# 1. Register admin via API
curl -X POST "https://api.yourdomain.com/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@yourdomain.com",
    "password": "YourSecurePassword123!",
    "name": "Admin"
  }'

# 2. Promote to admin
docker exec -it digiforge-mongodb mongosh digiforge --eval "
  db.users.updateOne(
    {email: 'admin@yourdomain.com'},
    {\$set: {is_admin: true}}
  )
"

# 3. Verify admin access
curl -X POST "https://api.yourdomain.com/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@yourdomain.com","password":"YourSecurePassword123!"}'
```

### 6. First Paying Customer

```bash
# After customer pays via Stripe/PayPal, credits are auto-added
# For manual activation (invoice/transfer):
./scripts/manage_customer.sh set-plan customer@email.com pro
./scripts/manage_customer.sh add-credits customer@email.com 200
```

### 7. Rollback Procedure

```bash
# Save current version
cd /opt/digiforge
git rev-parse HEAD > .rollback_point

# If issues occur, rollback:
git checkout $(cat .rollback_point)
docker compose -f docker-compose.nginx.yml build
docker compose -f docker-compose.nginx.yml up -d
```

### 8. Monitoring

```bash
# Health check
curl https://api.yourdomain.com/api/status

# Logs
docker compose logs -f backend

# Resource usage
docker stats --no-stream

# Database stats
docker exec digiforge-mongodb mongosh digiforge --eval "db.stats()"
```

### 9. Backup Schedule

```bash
# Ensure backup cron is active
crontab -l | grep backup

# Manual backup
./scripts/backup.sh

# Backup location
ls -la /opt/backups/digiforge/
```

---

## Payment Flow Summary

```
Customer Journey:
1. Register → Gets 10 free credits
2. Uses free credits to test product generation
3. Clicks "Upgrade" → Chooses plan (Starter/Pro/Enterprise)
4. Redirected to Stripe/PayPal checkout
5. Completes payment
6. Webhook/callback confirms payment
7. Credits automatically added to account
8. Confirmation email sent
9. Customer continues using service

Manual Payment Flow (invoice/transfer):
1. Customer contacts admin
2. Admin sends invoice/payment link
3. Customer pays
4. Admin runs: ./scripts/manage_customer.sh set-plan EMAIL pro
5. Customer receives credits
```

---

## Pricing Reference

| Plan | Price | Credits | Best For |
|------|-------|---------|----------|
| Free | €0 | 10 | Trial |
| Starter | €9.99/mo | 50 | Individuals |
| Pro | €29.99/mo | 200 | Freelancers |
| Enterprise | €99.99/mo | 1000 | Agencies |

---

## Support Contacts

- Technical Issues: Check `/var/log/supervisor/` logs
- Payment Issues: Check `db.payments` collection
- User Issues: Use `./scripts/manage_customer.sh`

---

**Deployment verified. Ready for production.**
