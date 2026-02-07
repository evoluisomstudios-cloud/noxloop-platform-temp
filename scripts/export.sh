#!/bin/bash

# ==============================================
# DigiForge Export Script
# Cria um arquivo ZIP com todo o código-fonte
# ==============================================

set -e

echo "🚀 DigiForge Export Script"
echo "=========================="

# Criar diretório temporário
EXPORT_DIR="/tmp/digiforge-export"
rm -rf "$EXPORT_DIR"
mkdir -p "$EXPORT_DIR"

echo "📁 A copiar ficheiros..."

# Copiar Backend
mkdir -p "$EXPORT_DIR/backend"
cp /app/backend/server.py "$EXPORT_DIR/backend/"
cp /app/backend/requirements.txt "$EXPORT_DIR/backend/"
cp /app/backend/Dockerfile "$EXPORT_DIR/backend/"
cp /app/backend/.env.example "$EXPORT_DIR/backend/"

# Copiar Frontend
mkdir -p "$EXPORT_DIR/frontend/src/pages"
mkdir -p "$EXPORT_DIR/frontend/src/components"
mkdir -p "$EXPORT_DIR/frontend/public"

cp /app/frontend/package.json "$EXPORT_DIR/frontend/"
cp /app/frontend/yarn.lock "$EXPORT_DIR/frontend/" 2>/dev/null || true
cp /app/frontend/tailwind.config.js "$EXPORT_DIR/frontend/"
cp /app/frontend/postcss.config.js "$EXPORT_DIR/frontend/"
cp /app/frontend/Dockerfile "$EXPORT_DIR/frontend/"
cp /app/frontend/nginx.conf "$EXPORT_DIR/frontend/"
cp /app/frontend/.env.example "$EXPORT_DIR/frontend/"

cp /app/frontend/src/*.js "$EXPORT_DIR/frontend/src/" 2>/dev/null || true
cp /app/frontend/src/*.css "$EXPORT_DIR/frontend/src/" 2>/dev/null || true
cp -r /app/frontend/src/pages/* "$EXPORT_DIR/frontend/src/pages/" 2>/dev/null || true
cp -r /app/frontend/src/components/* "$EXPORT_DIR/frontend/src/components/" 2>/dev/null || true
cp -r /app/frontend/public/* "$EXPORT_DIR/frontend/public/" 2>/dev/null || true

# Copiar Docker Compose
cp /app/docker-compose.yml "$EXPORT_DIR/"

# Copiar Documentação
mkdir -p "$EXPORT_DIR/docs"
cp /app/docs/*.md "$EXPORT_DIR/docs/" 2>/dev/null || true

# Copiar README
cp /app/memory/PRD.md "$EXPORT_DIR/PRD.md" 2>/dev/null || true

# Criar README principal
cat > "$EXPORT_DIR/README.md" << 'EOF'
# DigiForge - Plataforma de Produtos Digitais com IA

## 🚀 Quick Start

### Requisitos
- Docker & Docker Compose
- Conta OpenAI com API Key
- Conta Stripe (para pagamentos)

### Instalação Local

```bash
# 1. Configurar variáveis
cp backend/.env.example backend/.env
# Editar backend/.env com as tuas chaves

# 2. Build e run
docker compose up -d

# 3. Aceder
# Frontend: http://localhost:3000
# Backend: http://localhost:8001
```

### Documentação
- `docs/SELF_HOSTING_GUIDE.md` - Guia completo de deploy em VPS
- `docs/TECHNICAL_DOCUMENTATION.md` - Referência da API
- `docs/MARKETING_PLAN.md` - Plano de marketing

### Custo Estimado
- VPS: €4-12/mês
- OpenAI: €5-10/mês (100 gerações)
- Stripe: Apenas % por transação
- **Total: ~€15/mês**

---
Gerado por DigiForge - 100% Self-Hosted
EOF

# Criar arquivo ZIP
echo "📦 A criar arquivo ZIP..."
cd /tmp
zip -r digiforge-selfhosted.zip digiforge-export

# Mover para diretório acessível
mv /tmp/digiforge-selfhosted.zip /app/

echo ""
echo "✅ Export completo!"
echo "📍 Ficheiro: /app/digiforge-selfhosted.zip"
echo ""
echo "Para descarregar, usa:"
echo "  scp user@servidor:/app/digiforge-selfhosted.zip ."
