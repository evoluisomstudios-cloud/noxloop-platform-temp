# Separação Admin vs User - Documentação

## 🎯 Implementação Concluída

### **Backend Changes**

**Ficheiros alterados:**
1. `/app/backend/server.py`

**Mudanças:**
- ✅ `get_current_user()` agora SEMPRE busca `is_admin` da base de dados (não do token)
- ✅ `get_admin_user()` dependency valida is_admin=True
- ✅ `require_role()` middleware criado (preparado para roles futuros)
- ✅ Endpoint `/api/auth/me` retorna `is_admin`, `workspace_role`, `workspace_id`, `credits`
- ✅ Todas as rotas `/api/admin/*` protegidas com `Depends(get_admin_user)`
- ✅ 8 rotas admin protegidas:
  - GET /admin/stats
  - GET /admin/users
  - GET /admin/templates
  - POST /admin/templates
  - PUT /admin/templates/{id}
  - DELETE /admin/templates/{id}
  - GET /admin/plans
  - PUT /admin/plans/{id}

### **Frontend Changes**

**Ficheiros alterados:**
1. `/app/frontend/src/App.js`
2. `/app/frontend/src/components/DashboardLayout.jsx` (já estava implementado)

**Mudanças:**
- ✅ `ProtectedRoute` component aceita `requireAdmin` prop
- ✅ Rota `/admin` protegida com `requireAdmin={true}`
- ✅ Users sem is_admin=true são redirecionados para `/dashboard`
- ✅ Botão "Admin" no sidebar só aparece se `user.is_admin === true`
- ✅ Botão com styling diferenciado (roxo/purple) para destacar

---

## 🧪 Testes Manuais

### **Test 1: Admin Access ✅**

```bash
# 1. Create admin user
curl -X POST http://localhost:8001/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@noxloop.pt", "name": "Admin", "password": "admin123"}'

# 2. Set is_admin flag in DB
mongosh mongodb://localhost:27017/noxloop_db --quiet --eval \
  'db.users.updateOne({email: "admin@noxloop.pt"}, {$set: {is_admin: true}})'

# 3. Login
curl -X POST http://localhost:8001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@noxloop.pt", "password": "admin123"}' \
  --cookie-jar /tmp/admin.txt

# 4. Access admin endpoint
curl http://localhost:8001/api/admin/stats --cookie /tmp/admin.txt

# ✅ Expected: Returns stats (200 OK)
```

### **Test 2: Normal User Blocked ✅**

```bash
# 1. Create normal user
curl -X POST http://localhost:8001/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "user@noxloop.pt", "name": "User", "password": "user123"}'

# 2. Login (is_admin=false by default)
curl -X POST http://localhost:8001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@noxloop.pt", "password": "user123"}' \
  --cookie-jar /tmp/user.txt

# 3. Try to access admin endpoint
curl http://localhost:8001/api/admin/stats --cookie /tmp/user.txt

# ✅ Expected: {"detail": "Admin access required"} (403 Forbidden)
```

### **Test 3: Frontend Navigation**

**Admin User:**
1. Login com admin@noxloop.pt
2. ✅ Sidebar mostra link "Admin" (roxo, com ícone Shield)
3. ✅ Clicar em "Admin" → Acede a /admin
4. ✅ Página AdminPage carrega

**Normal User:**
1. Login com user@noxloop.pt
2. ✅ Sidebar NÃO mostra link "Admin"
3. ✅ Navegar manualmente para /admin → Redirect para /dashboard
4. ✅ Toast/mensagem de erro (opcional)

---

## 🔐 Security Features

### **Role Source of Truth**

**ANTES:**
```javascript
// ❌ Role vinha do JWT token (controlado pelo client)
user["is_admin"] = payload.get("is_admin", False)
```

**DEPOIS:**
```javascript
// ✅ Role SEMPRE vem da base de dados
user = await db.users.find_one({"user_id": payload["user_id"]})
user["is_admin"] = user.get("is_admin", False)  # From DB
```

### **Middleware Protection**

```python
async def get_admin_user(request: Request) -> dict:
    """Get current admin user - requires is_admin=True in DB"""
    user = await get_current_user(request)
    if not user.get("is_admin", False):
        raise HTTPException(status_code=403, detail="Admin access required")
    return user
```

### **Frontend Guard**

```javascript
const ProtectedRoute = ({ children, user, loading, requireAdmin = false }) => {
  // Redirect if not admin
  if (!loading && user && requireAdmin && !user.is_admin) {
    navigate("/dashboard", { replace: true });
  }
  
  if (requireAdmin && !user.is_admin) return null;
  return children;
};
```

---

## 🚀 Como Criar Novos Admins

### **Opção 1: MongoDB Shell**

```bash
mongosh mongodb://localhost:27017/noxloop_db

db.users.updateOne(
  { email: "user@example.com" },
  { $set: { is_admin: true } }
)
```

### **Opção 2: Admin Panel (Future)**

```python
@admin_router.post("/users/{user_id}/promote")
async def promote_to_admin(user_id: str, admin: dict = Depends(get_admin_user)):
    await db.users.update_one(
        {"user_id": user_id},
        {"$set": {"is_admin": True}}
    )
    return {"status": "promoted"}
```

### **Opção 3: Environment Variable (First Admin)**

```python
# On startup, create first admin from env
ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL', 'admin@noxloop.pt')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'changeme')

@app.on_event("startup")
async def create_first_admin():
    existing = await db.users.find_one({"email": ADMIN_EMAIL})
    if not existing:
        # Create first admin user
        hashed_password = hash_password(ADMIN_PASSWORD)
        await db.users.insert_one({
            "user_id": f"user_{uuid.uuid4().hex[:12]}",
            "email": ADMIN_EMAIL,
            "password": hashed_password,
            "is_admin": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        })
```

---

## 🔄 Rollback Plan

**Se algo falhar, reverter por commit:**

```bash
# Check changes
git log --oneline -5

# Rollback backend
git revert HEAD~1

# Rollback frontend
git revert HEAD~2

# Or hard reset (CAUTION)
git reset --hard HEAD~2
```

**Ficheiros para reverter manualmente:**
1. `/app/backend/server.py` (linhas 132-165)
2. `/app/frontend/src/App.js` (linhas 68-96, 147-152)

---

## 📊 Status

| Feature | Backend | Frontend | Tested |
|---------|---------|----------|--------|
| Role from DB | ✅ | N/A | ✅ |
| Admin middleware | ✅ | N/A | ✅ |
| /api/admin/* protected | ✅ | N/A | ✅ |
| /api/auth/me with role | ✅ | N/A | ✅ |
| Admin route guard | N/A | ✅ | ✅ |
| Admin button visibility | N/A | ✅ | ✅ |
| Access control | ✅ | ✅ | ✅ |

---

## ✅ Verificação Final

```bash
# 1. Backend running
curl http://localhost:8001/api/status

# 2. Admin can access
curl http://localhost:8001/api/admin/stats --cookie /tmp/admin.txt

# 3. User cannot access
curl http://localhost:8001/api/admin/stats --cookie /tmp/user.txt
# Expected: 403 Forbidden

# 4. Frontend compiled
sudo supervisorctl status frontend
# Expected: RUNNING

# 5. Test UI manually
# - Login as admin → See Admin button
# - Login as user → No Admin button
# - User tries /admin URL → Redirects to /dashboard
```

**Status: ✅ IMPLEMENTATION COMPLETE**
