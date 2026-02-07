# 🧪 NOXLOOP - Smoke Test (End-to-End QA)

## Objetivo
Validar que o fluxo comercial completo funciona corretamente antes de deploy em produção.

---

## ✅ PRÉ-REQUISITOS

1. **Serviços a correr:**
   ```bash
   docker-compose up -d
   # OU
   sudo supervisorctl status
   # Deve mostrar: backend RUNNING, frontend RUNNING, mongodb RUNNING
   ```

2. **Env vars configuradas:**
   - JWT_SECRET_KEY (não default)
   - MONGO_URL
   - STRIPE_API_KEY (test key: sk_test_...)
   - OPENAI_API_KEY (ou mock)

3. **Stripe Webhook configurado:**
   - Endpoint: https://yourdomain.com/api/billing/webhook/stripe
   - Eventos: checkout.session.completed, invoice.payment_succeeded

---

## 🔍 TESTE 1: HEALTH CHECK

```bash
curl http://localhost:8001/api/health | jq .

# ✅ Deve retornar:
{
  "status": "healthy",
  "checks": {
    "database": {"status": "healthy", "connected": true},
    "configuration": {"status": "healthy" | "warning"},
    "storage": {"status": "healthy", "writable": true},
    "data": {"users": X, "products": Y, "workspaces": Z}
  }
}
```

**Validar:**
- [ ] status = "healthy"
- [ ] database.connected = true
- [ ] storage.writable = true

---

## 🔍 TESTE 2: REGISTO & AUTH

### 2.1 Criar utilizador normal

```bash
curl -X POST http://localhost:8001/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@test.com",
    "name": "Test User",
    "password": "test123456"
  }' | jq .
```

**Validar:**
- [ ] Status 200 OK
- [ ] Retorna user_id, email
- [ ] is_admin = false

### 2.2 Login

```bash
curl -X POST http://localhost:8001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@test.com",
    "password": "test123456"
  }' \
  --cookie-jar /tmp/test_cookies.txt | jq .
```

**Validar:**
- [ ] Status 200 OK
- [ ] Cookie "session_token" setado
- [ ] Retorna workspaces

### 2.3 Ver perfil

```bash
curl http://localhost:8001/api/auth/me \
  --cookie /tmp/test_cookies.txt | jq .
```

**Validar:**
- [ ] user_id, email, name corretos
- [ ] is_admin = false
- [ ] credits = 10 (free plan)
- [ ] workspace_id presente

---

## 🔍 TESTE 3: SISTEMA DE CRÉDITOS

### 3.1 Verificar créditos iniciais

```bash
curl http://localhost:8001/api/auth/me \
  --cookie /tmp/test_cookies.txt | jq '{credits, plan}'

# ✅ Deve mostrar: credits=10, plan="free"
```

### 3.2 Gerar produto (consome 5 créditos)

```bash
WORKSPACE_ID=$(curl -s http://localhost:8001/api/auth/me --cookie /tmp/test_cookies.txt | jq -r '.workspaces[0].workspace_id')

curl -X POST "http://localhost:8001/api/workspaces/$WORKSPACE_ID/products/generate" \
  --cookie /tmp/test_cookies.txt \
  -H "Content-Type: application/json" \
  -d '{
    "title": "eBook: Teste Marketing",
    "description": "eBook de teste",
    "product_type": "ebook",
    "topic": "Marketing Digital",
    "target_audience": "Empresários"
  }' | jq '{product_id, title, status}'
```

**Validar:**
- [ ] Status 200 OK (se credits >= 5)
- [ ] Status 402 Payment Required (se credits < 5)
- [ ] Produto criado com status="draft"

### 3.3 Verificar créditos após geração

```bash
curl http://localhost:8001/api/auth/me \
  --cookie /tmp/test_cookies.txt | jq .credits

# ✅ Deve mostrar: credits=5 (10 - 5)
```

### 3.4 Tentar gerar outro produto

```bash
# (repetir comando 3.2)
# ✅ Deve funcionar (5 - 5 = 0)
```

### 3.5 Tentar gerar sem créditos

```bash
# (repetir comando 3.2 pela 3ª vez)
# ✅ Deve retornar: 402 {"detail": "Créditos insuficientes. Necessário: 5, Disponível: 0"}
```

---

## 🔍 TESTE 4: PUBLICAÇÃO DE PRODUTO

### 4.1 Listar produtos (privado)

```bash
curl "http://localhost:8001/api/workspaces/$WORKSPACE_ID/products" \
  --cookie /tmp/test_cookies.txt | jq '.[0] | {product_id, title, status, slug}'
```

**Validar:**
- [ ] Lista contém produtos
- [ ] status = "draft"
- [ ] slug = null

### 4.2 Publicar produto

```bash
PRODUCT_ID=$(curl -s "http://localhost:8001/api/workspaces/$WORKSPACE_ID/products" --cookie /tmp/test_cookies.txt | jq -r '.[0].product_id')

curl -X PUT "http://localhost:8001/api/workspaces/$WORKSPACE_ID/products/$PRODUCT_ID" \
  --cookie /tmp/test_cookies.txt \
  -H "Content-Type: application/json" \
  -d '{
    "status": "published",
    "price": 19.99
  }' | jq '{product_id, status, slug, public_url}'
```

**Validar:**
- [ ] status = "published"
- [ ] is_published = true
- [ ] slug gerado (ex: "ebook-teste-marketing")
- [ ] public_url = "/p/ebook-teste-marketing"

---

## 🔍 TESTE 5: CATÁLOGO PÚBLICO

### 5.1 Listar produtos públicos (SEM AUTH)

```bash
curl http://localhost:8001/api/public/products | jq '{total, count: (.products | length)}'
```

**Validar:**
- [ ] Retorna produtos com is_published=true
- [ ] NÃO retorna produtos draft
- [ ] NÃO expõe workspace_id, user_id, content

### 5.2 Ver produto por slug (SEM AUTH)

```bash
curl "http://localhost:8001/api/public/product/slug/ebook-teste-marketing" | jq '{title, slug, price, is_published}'
```

**Validar:**
- [ ] Status 200 OK
- [ ] Dados do produto visíveis
- [ ] views incrementado

### 5.3 Tentar ver produto draft (SEM AUTH)

```bash
# (usar slug de produto draft)
curl "http://localhost:8001/api/public/product/slug/produto-draft" 

# ✅ Deve retornar: 404 {"detail": "Produto não encontrado ou não publicado"}
```

---

## 🔍 TESTE 6: COMPRA (STRIPE TEST MODE)

**⚠️ Requer Stripe test keys configuradas**

### 6.1 Iniciar checkout

```bash
# Login primeiro
curl -X POST http://localhost:8001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "buyer@test.com", "password": "buyer123"}' \
  --cookie-jar /tmp/buyer_cookies.txt

# Criar checkout
curl -X POST "http://localhost:8001/api/products/$PRODUCT_ID/purchase" \
  --cookie /tmp/buyer_cookies.txt \
  -H "Content-Type: application/json" \
  -d '{"origin_url": "http://localhost:3000"}' | jq '{checkout_url}'
```

**Validar:**
- [ ] Retorna checkout_url (Stripe hosted)
- [ ] Purchase record criado na DB com status="pending"

### 6.2 Simular pagamento (Stripe CLI)

```bash
stripe listen --forward-to localhost:8001/api/billing/webhook/stripe

# Em outro terminal, trigger checkout.session.completed
stripe trigger checkout.session.completed
```

### 6.3 Verificar acesso após pagamento

```bash
curl "http://localhost:8001/api/purchases/verify?session_id=cs_test_xxx" \
  --cookie /tmp/buyer_cookies.txt | jq '{status, access_granted}'
```

**Validar:**
- [ ] status = "completed"
- [ ] access_granted = true
- [ ] product.downloads incrementado
- [ ] purchase.status = "completed" na DB

### 6.4 Ver minhas compras

```bash
curl "http://localhost:8001/api/purchases/my" \
  --cookie /tmp/buyer_cookies.txt | jq '.[0] | {product_title, amount, access_granted}'
```

**Validar:**
- [ ] Lista contém compra recente
- [ ] Todos os campos corretos

---

## 🔍 TESTE 7: PLANOS & RENOVAÇÃO

### 7.1 Listar planos

```bash
curl http://localhost:8001/api/billing/plans | jq '.[] | {name, price, credits_monthly}'
```

**Validar:**
- [ ] Free: 10 créditos
- [ ] Starter: 50 créditos (€9.99)
- [ ] Pro: 200 créditos (€29.99)
- [ ] Enterprise: 1000 créditos (€99.99)

### 7.2 Assinar plano Starter

```bash
curl -X POST http://localhost:8001/api/billing/checkout/stripe \
  --cookie /tmp/test_cookies.txt \
  -H "Content-Type: application/json" \
  -d '{
    "plan_id": "starter",
    "payment_method": "stripe",
    "success_url": "http://localhost:3000/purchase/success",
    "cancel_url": "http://localhost:3000/dashboard"
  }' | jq '{url}'
```

**Validar:**
- [ ] Retorna Stripe checkout URL
- [ ] Metadata contém: user_id, plan_id, credits

### 7.3 Webhook renovação mensal (simulate)

```bash
stripe trigger invoice.payment_succeeded
```

**Validar:**
- [ ] Créditos do workspace resetados para credits_monthly do plano
- [ ] Log: "Renewed X credits for workspace..."

---

## 🔍 TESTE 8: ADMIN vs USER

### 8.1 User normal tenta aceder admin

```bash
curl http://localhost:8001/api/admin/stats \
  --cookie /tmp/test_cookies.txt

# ✅ Deve retornar: 403 {"detail": "Admin access required"}
```

### 8.2 Admin acede stats

```bash
# Criar admin
mongosh mongodb://localhost:27017/noxloop_db --quiet --eval \
  'db.users.updateOne({email: "admin@noxloop.pt"}, {$set: {is_admin: true}})'

# Login como admin
curl -X POST http://localhost:8001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@noxloop.pt", "password": "admin123"}' \
  --cookie-jar /tmp/admin_cookies.txt

# Aceder stats
curl http://localhost:8001/api/admin/stats \
  --cookie /tmp/admin_cookies.txt | jq .
```

**Validar:**
- [ ] Admin consegue aceder
- [ ] Retorna: total_users, total_products, revenue, etc.

---

## 🔍 TESTE 9: IDEMPOTÊNCIA WEBHOOKS

### 9.1 Enviar mesmo evento 2x

```bash
# Capturar event_id de um webhook Stripe
# Enviar payload duplicado

# ✅ 1ª chamada: processa normalmente
# ✅ 2ª chamada: retorna {"status": "already_processed"}
# ✅ Créditos NÃO são duplicados
```

**Validar:**
- [ ] webhook_events collection contém event_id
- [ ] Duplicado não é processado

---

## 🔍 TESTE 10: EMAIL RESILIENCE

### 10.1 SMTP desativado

```bash
# Em .env: SMTP_ENABLED=false

# Tentar registar user
curl -X POST http://localhost:8001/api/auth/register ...

# ✅ Registo funciona normalmente
# ✅ Logs mostram: "SMTP disabled - would send..."
# ✅ Sistema NÃO crashar
```

### 10.2 SMTP com credenciais erradas

```bash
# Em .env: SMTP_ENABLED=true, SMTP_PASSWORD=wrong

# Tentar registar user
curl -X POST http://localhost:8001/api/auth/register ...

# ✅ Registo funciona (email falha mas não bloqueia)
# ✅ Log mostra: "✗ SMTP authentication failed"
```

---

## 🔍 TESTE 11: SEGURANÇA MEDIA ASSETS

### 11.1 User normal tenta upload

```bash
curl -X POST http://localhost:8001/api/admin/media/upload \
  --cookie /tmp/test_cookies.txt \
  -F "file=@test.jpg"

# ✅ Deve retornar: 403 Forbidden
```

### 11.2 Admin faz upload

```bash
curl -X POST http://localhost:8001/api/admin/media/upload \
  --cookie /tmp/admin_cookies.txt \
  -F "file=@test.jpg" | jq '{asset_id, filename, secure_url}'
```

**Validar:**
- [ ] Status 200 OK
- [ ] asset_id gerado
- [ ] File salvo em /uploads com nome seguro
- [ ] DB record criado

### 11.3 Download público de media

```bash
ASSET_ID=$(curl -s http://localhost:8001/api/admin/media --cookie /tmp/admin_cookies.txt | jq -r '.assets[0].asset_id')

# Download SEM auth - Endpoint PÚBLICO
curl "http://localhost:8001/api/media/$ASSET_ID" -o /tmp/downloaded.jpg

# ✅ File downloaded (endpoint público)
```

### 11.4 Associar media a produto

```bash
curl -X PUT "http://localhost:8001/api/products/$PRODUCT_ID" \
  --cookie /tmp/admin_cookies.txt \
  -H "Content-Type: application/json" \
  -d '{
    "media_asset_ids": ["'"$ASSET_ID"'"]
  }' | jq '{product_id, media_asset_ids}'

# ✅ media_asset_ids guardados no produto
```

### 11.5 Verificar imagem na página pública

```bash
curl -s "http://localhost:8001/api/public/product/$PRODUCT_ID" | jq '{title, media_asset_ids}'

# ✅ media_asset_ids presente
# A primeira imagem será mostrada como hero image no frontend
```

---

## 🔍 TESTE 12: FRONTEND UI

### 12.1 Landing page

```
Abrir: http://localhost:3000/

Validar:
- [ ] Branding "NOXLOOP" visível no navbar
- [ ] ZERO badges "Made with Emergent" ou "Powered by GPT"
- [ ] Texto em PT-PT
- [ ] CTAs "Criar conta" funcionam
```

### 12.2 Auth page

```
Abrir: http://localhost:3000/auth

Validar:
- [ ] Logo "NOXLOOP" no topo
- [ ] Tabs Login/Registar funcionam
- [ ] Registar novo user → redireciona para /dashboard
```

### 12.3 Dashboard

```
Login e abrir: http://localhost:3000/dashboard

Validar:
- [ ] Créditos visíveis no header
- [ ] Links: Dashboard, Produtos, Campanhas, Analytics, Definições
- [ ] Se admin: link "Admin" visível (roxo)
- [ ] Se user normal: link "Admin" NÃO visível
```

### 12.4 Catálogo público

```
Abrir: http://localhost:3000/produtos

Validar:
- [ ] Lista de produtos published
- [ ] Filtros por tipo funcionam
- [ ] Cards mostram: título, descrição, preço, views
- [ ] Botão "Ver Detalhes" funciona
```

### 12.5 Produto individual

```
Abrir: http://localhost:3000/p/ebook-marketing-digital-completo

Validar:
- [ ] Produto carrega corretamente
- [ ] Preço visível
- [ ] Botão "Comprar" presente
- [ ] Views incrementadas
```

### 12.6 Admin panel (só admin)

```
Login como admin e abrir: http://localhost:3000/admin

Validar:
- [ ] Página carrega (se admin)
- [ ] Redireciona para /dashboard (se user normal)
- [ ] Stats visíveis: users, products, revenue
```

---

## 🔍 TESTE 13: END-TO-END COMPLETO

### Cenário: Cliente novo compra produto

1. **Abrir landing** → http://localhost:3000
2. **Clicar "Criar conta"**
3. **Registar:** buyer@test.com / buyer123
4. **Aguardar redirect** → /dashboard
5. **Ver créditos:** 10 créditos visíveis
6. **Ir para "Produtos"**
7. **Clicar "Criar Novo Produto"**
8. **Preencher form e gerar** (consome 5 créditos)
9. **Aguardar geração** (10-30s com OpenAI, instantâneo com mock)
10. **Editar produto:** definir preço €29.99
11. **Clicar "Publicar"**
12. **Copiar public_url** → /p/nome-do-produto
13. **Abrir em janela anónima:** http://localhost:3000/p/nome-do-produto
14. **Clicar "Comprar"**
15. **Fazer login** (se pedido)
16. **Redirect para Stripe checkout**
17. **Usar test card:** 4242 4242 4242 4242, qualquer CVC/data futura
18. **Completar pagamento**
19. **Redirect para** /purchase/success
20. **Ver produto comprado** → acesso garantido

**Validações finais:**
- [ ] Purchase record na DB: status="completed", access_granted=true
- [ ] Produto stats: downloads +1, revenue +€29.99
- [ ] Email confirmação enviado (se SMTP enabled)
- [ ] Webhook event guardado na DB (idempotency)

---

## 🔍 TESTE 14: WEBHOOK IDEMPOTENCY

```bash
# Capturar um webhook real do Stripe
# Reenviar o mesmo payload 2x

# 1ª vez:
curl -X POST http://localhost:8001/api/billing/webhook/stripe \
  -H "Stripe-Signature: xxx" \
  -d @webhook_payload.json

# ✅ Processa: créditos adicionados

# 2ª vez (mesmo event.id):
curl -X POST http://localhost:8001/api/billing/webhook/stripe \
  -H "Stripe-Signature: xxx" \
  -d @webhook_payload.json

# ✅ Retorna: {"status": "already_processed"}
# ✅ Créditos NÃO duplicados
```

**Validar:**
- [ ] Collection `webhook_events` contém event_id
- [ ] Duplicado ignorado

---

## 📊 CHECKLIST FINAL

### Configuração
- [ ] JWT_SECRET_KEY não é default
- [ ] MONGO_URL correto
- [ ] Stripe keys configuradas (test ou live)
- [ ] OpenAI key configurada (ou mock aceite)
- [ ] SMTP configurado (opcional mas recomendado)

### Funcionalidades Core
- [ ] Registo + Login funcionam
- [ ] Créditos grátis (10) atribuídos
- [ ] Geração consome créditos (5 por produto)
- [ ] Bloqueio quando credits = 0
- [ ] Publicação gera slug único
- [ ] Catálogo público só mostra published

### Pagamentos
- [ ] Stripe checkout funciona
- [ ] Webhook processa pagamentos
- [ ] Acesso garantido após payment
- [ ] Idempotência webhooks OK
- [ ] Renovação mensal reseta créditos

### Segurança
- [ ] Admin routes protegidas (403 para users)
- [ ] /admin UI redirect não-admins
- [ ] Media upload só para admin
- [ ] Download media requer auth
- [ ] Role vem sempre da DB (não do token)

### Resiliência
- [ ] Email failure não crashar app
- [ ] Health check retorna status correto
- [ ] Logs claros de erros
- [ ] Env vars validadas no startup

### UI/UX
- [ ] ZERO branding externo (Emergent/ChatGPT)
- [ ] Branding "NOXLOOP" consistente
- [ ] Texto 100% PT-PT
- [ ] Links todos funcionais
- [ ] Mobile responsive

---

## ✅ CRITÉRIO DE SUCESSO

**Se TODOS os testes acima passam:**
→ Plataforma pronta para produção ✅

**Se algum teste falha:**
→ Corrigir antes de deploy ❌

---

## 🚨 TROUBLESHOOTING

### Backend não inicia
```bash
tail -n 50 /var/log/supervisor/backend.err.log
# Check: syntax errors, import errors, env vars
```

### Database connection fails
```bash
mongosh mongodb://localhost:27017/noxloop_db
# Check: MongoDB running, credentials corretos
```

### Stripe webhooks não funcionam
```bash
# 1. Verificar STRIPE_WEBHOOK_SECRET configurado
# 2. Testar signature verification
# 3. Check logs: /var/log/supervisor/backend.out.log
```

### Frontend não compila
```bash
cd /app/frontend
yarn install
yarn build
# Check: package.json, node version, dependencies
```

---

## 📝 REPORT TEMPLATE

Após executar todos os testes, preencher:

```
NOXLOOP Smoke Test Report
Data: ___________
Tester: ___________
Environment: Development / Staging / Production

✅ PASSED: ___/14 testes
❌ FAILED: ___/14 testes

Failures:
- [Teste X]: Descrição do erro
- [Teste Y]: Descrição do erro

Critical Issues: ___
Warnings: ___
Recommendations: ___

Sign-off: ____________
```

---

## 🎯 PRÓXIMOS PASSOS

Após todos os testes passarem:
1. Fazer deploy em staging
2. Repetir smoke test em staging
3. Configurar monitoring (Sentry, LogRocket)
4. Deploy em produção
5. Smoke test final em produção
6. 🎉 Launch!

---

© 2025 NOXLOOP - Smoke Test Documentation v1.0
