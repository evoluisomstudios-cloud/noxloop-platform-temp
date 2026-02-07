#!/bin/bash
# ============================================
# DigiForge Production Checklist
# Run: ./production_checklist.sh
# ============================================

echo "=========================================="
echo "DigiForge Production Checklist"
echo "=========================================="
echo ""

# Configuração - ajusta estes valores
DOMAIN="${DOMAIN:-localhost}"
API_DOMAIN="${API_DOMAIN:-localhost:8001}"

PASS=0
FAIL=0
WARN=0

check_pass() {
    echo "✅ PASS"
    ((PASS++))
}

check_fail() {
    echo "❌ FAIL"
    ((FAIL++))
}

check_warn() {
    echo "⚠️ WARNING: $1"
    ((WARN++))
}

# 1. Docker containers running
echo -n "1. Docker containers: "
if docker ps 2>/dev/null | grep -q "digiforge-caddy" && \
   docker ps 2>/dev/null | grep -q "digiforge-backend" && \
   docker ps 2>/dev/null | grep -q "digiforge-frontend" && \
   docker ps 2>/dev/null | grep -q "digiforge-mongodb"; then
    check_pass
else
    # Check for dev mode (without caddy)
    if docker ps 2>/dev/null | grep -q "digiforge-backend" && \
       docker ps 2>/dev/null | grep -q "digiforge-mongodb"; then
        check_warn "Running in dev mode (no Caddy)"
    else
        check_fail
    fi
fi

# 2. Firewall configured
echo -n "2. Firewall: "
if command -v ufw &> /dev/null; then
    if sudo ufw status 2>/dev/null | grep -q "80/tcp.*ALLOW"; then
        check_pass
    else
        check_warn "UFW not configured for port 80"
    fi
else
    check_warn "UFW not installed"
fi

# 3. SSL certificate (only if using Caddy)
echo -n "3. SSL certificate: "
if docker ps 2>/dev/null | grep -q "digiforge-caddy"; then
    if curl -sI "https://$DOMAIN" 2>/dev/null | grep -q "200\|301\|302"; then
        check_pass
    else
        check_warn "SSL may not be configured yet"
    fi
else
    check_warn "Caddy not running (dev mode)"
fi

# 4. API responding
echo -n "4. API status: "
# Try HTTPS first, then HTTP
API_STATUS=$(curl -s "https://$API_DOMAIN/api/status" 2>/dev/null || curl -s "http://$API_DOMAIN/api/status" 2>/dev/null || curl -s "http://localhost:8001/api/status" 2>/dev/null)
if echo "$API_STATUS" | grep -q "database_connected.*true"; then
    check_pass
else
    check_fail
fi

# 5. LLM provider configured
echo -n "5. LLM provider: "
LLM=$(echo "$API_STATUS" | grep -o '"llm_provider":"[^"]*"' | cut -d'"' -f4)
if [ -n "$LLM" ]; then
    echo "✅ $LLM"
    ((PASS++))
else
    check_warn "Could not determine LLM provider"
fi

# 6. Frontend loading
echo -n "6. Frontend: "
FRONTEND_STATUS=$(curl -sI "https://$DOMAIN" 2>/dev/null || curl -sI "http://$DOMAIN" 2>/dev/null || curl -sI "http://localhost:3000" 2>/dev/null)
if echo "$FRONTEND_STATUS" | grep -q "200"; then
    check_pass
else
    check_warn "Frontend may not be accessible externally"
fi

# 7. Admin user exists
echo -n "7. Admin user: "
ADMIN_COUNT=$(docker exec digiforge-mongodb mongosh digiforge --quiet --eval "db.users.countDocuments({is_admin: true})" 2>/dev/null)
if [ "$ADMIN_COUNT" -gt 0 ] 2>/dev/null; then
    echo "✅ PASS ($ADMIN_COUNT admin(s))"
    ((PASS++))
else
    check_warn "No admin users found"
fi

# 8. Backups configured
echo -n "8. Backups cron: "
if crontab -l 2>/dev/null | grep -q "backup.sh"; then
    check_pass
else
    check_warn "Backup cron not configured"
fi

# 9. Disk space
echo -n "9. Disk space: "
DISK_USE=$(df -h / 2>/dev/null | tail -1 | awk '{print $5}' | sed 's/%//')
if [ -n "$DISK_USE" ] && [ "$DISK_USE" -lt 80 ] 2>/dev/null; then
    echo "✅ PASS (${DISK_USE}% used)"
    ((PASS++))
else
    check_warn "${DISK_USE:-unknown}% disk used"
fi

# 10. Memory
echo -n "10. Memory: "
MEM_FREE=$(free -m 2>/dev/null | awk '/^Mem:/ {print $7}')
if [ -n "$MEM_FREE" ] && [ "$MEM_FREE" -gt 500 ] 2>/dev/null; then
    echo "✅ PASS (${MEM_FREE}MB available)"
    ((PASS++))
else
    check_warn "${MEM_FREE:-unknown}MB available"
fi

echo ""
echo "=========================================="
echo "Results: $PASS passed, $FAIL failed, $WARN warnings"
echo "=========================================="

if [ "$FAIL" -gt 0 ]; then
    exit 1
fi
