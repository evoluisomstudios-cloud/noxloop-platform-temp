#!/bin/bash
# ============================================
# DigiForge Health Check Script
# Run: ./healthcheck.sh
# ============================================

# Configuração - ajusta conforme o teu setup
API_URL="${API_URL:-http://localhost:8001}"

echo "=== DigiForge Health Check ==="
echo "Data: $(date)"
echo ""

# Verificar containers
echo "=== Docker Containers ==="
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null | grep digiforge || echo "No containers found"

echo ""

# Verificar API
echo "=== API Status ==="
RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" "$API_URL/api/status" 2>/dev/null)
HTTP_CODE=$(echo "$RESPONSE" | grep "HTTP_CODE" | cut -d: -f2)
BODY=$(echo "$RESPONSE" | grep -v "HTTP_CODE")

if [ "$HTTP_CODE" = "200" ]; then
    echo "✅ API OK (HTTP $HTTP_CODE)"
    echo "$BODY" | python3 -m json.tool 2>/dev/null || echo "$BODY"
else
    echo "❌ API FAILED (HTTP $HTTP_CODE)"
fi

echo ""

# Uso de recursos
echo "=== Resource Usage ==="
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}" 2>/dev/null | grep digiforge || echo "No containers running"

echo ""

# Espaço em disco
echo "=== Disk Usage ==="
df -h / | tail -1
echo ""
docker system df 2>/dev/null || echo "Docker not available"

echo ""
echo "=== Health Check Complete ==="
