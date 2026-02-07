"""
# NOXLOOP - AI Digital Product Platform
100% Self-Hosted SaaS Application

Version: 2.0.0
"""
from fastapi import FastAPI, APIRouter, HTTPException, Request, Depends, Response
from fastapi.responses import JSONResponse, StreamingResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import io
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone, timedelta
import jwt
import bcrypt
import httpx

# Load environment variables
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Import services
from services import llm_service, rag_client, webhook_service, campaign_builder
from services import payment_service, email_service, security_service
from models.schemas import (
    UserCreate, UserLogin, UserResponse, UserWithWorkspaces,
    WorkspaceCreate, WorkspaceUpdate, WorkspaceResponse, WorkspaceMember, WorkspaceInvite,
    ProductCreate, ProductUpdate, ProductResponse, ProductStatus,
    CampaignCreate, CampaignResponse,
    TemplateCreate, TemplateUpdate, TemplateResponse,
    PlanConfig, PlanUpdate, PlanType, FeatureFlag, UserRole,
    CheckoutRequest, SubscriptionRequest, GoogleAuthRequest,
    AdminStats, SystemStatus, UsageRecord,
    PurchaseCreate, PurchaseResponse,
    MediaAssetType, MediaAssetCreate, MediaAssetResponse
)

# ==================== DATABASE ====================
mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ.get('DB_NAME', 'noxloop')]

# ==================== CONFIGURATION ====================
JWT_SECRET = os.environ.get('JWT_SECRET_KEY', 'change-this-secret-key')
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 168  # 7 days

# Stripe (optional)
STRIPE_ENABLED = os.environ.get('STRIPE_ENABLED', 'false').lower() == 'true'
if STRIPE_ENABLED:
    import stripe
    stripe.api_key = os.environ.get('STRIPE_API_KEY')

# Google OAuth (optional)
GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET')

# Admin credentials
ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL', 'admin@noxloop.pt')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'admin123')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)



# ==================== ENVIRONMENT VALIDATION ====================

def validate_environment():
    """Validate critical environment variables on startup"""
    errors = []
    warnings = []
    
    # Critical vars
    if not os.environ.get('MONGO_URL'):
        errors.append("MONGO_URL not configured")
    
    if not os.environ.get('JWT_SECRET_KEY') or os.environ.get('JWT_SECRET_KEY') == 'your-secret-key':
        errors.append("JWT_SECRET_KEY not configured or using default (INSECURE)")
    
    # Production warnings
    if os.environ.get('STRIPE_ENABLED', 'false').lower() == 'true':
        if not os.environ.get('STRIPE_API_KEY'):
            warnings.append("STRIPE_ENABLED=true but STRIPE_API_KEY not set")
        if not os.environ.get('STRIPE_WEBHOOK_SECRET'):
            warnings.append("STRIPE_ENABLED=true but STRIPE_WEBHOOK_SECRET not set (webhooks will fail)")
    
    if os.environ.get('SMTP_ENABLED', 'false').lower() == 'true':
        required_smtp = ['SMTP_HOST', 'SMTP_PORT', 'SMTP_USER', 'SMTP_PASSWORD']
        for var in required_smtp:
            if not os.environ.get(var):
                warnings.append(f"SMTP_ENABLED=true but {var} not set")
    
    if not os.environ.get('OPENAI_API_KEY') and os.environ.get('LLM_PROVIDER') == 'openai':
        warnings.append("LLM_PROVIDER=openai but OPENAI_API_KEY not set (will use mock)")
    
    # Log results
    if errors:
        logger.error("❌ CRITICAL CONFIGURATION ERRORS:")
        for error in errors:
            logger.error(f"  - {error}")
        raise RuntimeError(f"Configuration errors: {', '.join(errors)}")
    
    if warnings:
        logger.warning("⚠️  CONFIGURATION WARNINGS:")
        for warning in warnings:
            logger.warning(f"  - {warning}")
    
    logger.info("✅ Environment validation passed")

# ==================== APP SETUP ====================
app = FastAPI(
    title="NOXLOOP",
    description="AI-Powered Digital Product Platform - 100% Self-Hosted",
    version="2.0.0"
)



# Helper function to generate slug
def generate_slug(title: str) -> str:
    """Generate URL-friendly slug from title"""
    slug = title.lower()
    slug = re.sub(r'[^a-z0-9\s-]', '', slug)
    slug = re.sub(r'\s+', '-', slug)
    slug = re.sub(r'-+', '-', slug)
    slug = slug.strip('-')
    return slug[:50]  # Max 50 chars


# Media upload configuration
UPLOAD_DIR = Path("/app/uploads")
UPLOAD_DIR.mkdir(exist_ok=True)
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp"}
ALLOWED_VIDEO_TYPES = {"video/mp4", "video/webm", "video/quicktime"}
ALLOWED_DOCUMENT_TYPES = {"application/pdf"}
ALLOWED_MIME_TYPES = ALLOWED_IMAGE_TYPES | ALLOWED_VIDEO_TYPES | ALLOWED_DOCUMENT_TYPES

def generate_secure_filename(original_filename: str) -> str:
    """Generate secure unique filename"""
    ext = Path(original_filename).suffix
    unique_id = uuid.uuid4().hex[:16]
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d")
    return f"{timestamp}_{unique_id}{ext}"

def get_asset_type(mime_type: str) -> MediaAssetType:
    """Determine asset type from MIME type"""
    if mime_type in ALLOWED_IMAGE_TYPES:
        return MediaAssetType.IMAGE
    elif mime_type in ALLOWED_VIDEO_TYPES:
        return MediaAssetType.VIDEO
    elif mime_type in ALLOWED_DOCUMENT_TYPES:
        return MediaAssetType.DOCUMENT
    raise ValueError(f"Unsupported MIME type: {mime_type}")


api_router = APIRouter(prefix="/api")
admin_router = APIRouter(prefix="/api/admin")

# ==================== DEFAULT PLANS ====================
DEFAULT_PLANS = {
    PlanType.FREE: {
        "name": "Free",
        "price": 0,
        "credits_monthly": 10,
        "features": [],
        "max_workspaces": 1,
        "max_members_per_workspace": 1
    },
    PlanType.STARTER: {
        "name": "Starter",
        "price": 9.99,
        "credits_monthly": 50,
        "features": [FeatureFlag.CUSTOM_TEMPLATES],
        "max_workspaces": 3,
        "max_members_per_workspace": 3
    },
    PlanType.PRO: {
        "name": "Pro",
        "price": 29.99,
        "credits_monthly": 200,
        "features": [FeatureFlag.UNLIMITED_EXPORTS, FeatureFlag.PRIORITY_GENERATION, FeatureFlag.CUSTOM_TEMPLATES, FeatureFlag.RAG_ACCESS],
        "max_workspaces": 10,
        "max_members_per_workspace": 10
    },
    PlanType.ENTERPRISE: {
        "name": "Enterprise",
        "price": 99.99,
        "credits_monthly": 1000,
        "features": [f for f in FeatureFlag],
        "max_workspaces": 100,
        "max_members_per_workspace": 100
    }
}

# ==================== AUTH HELPERS ====================

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_jwt_token(user_id: str, email: str, is_admin: bool = False) -> str:
    payload = {
        "user_id": user_id,
        "email": email,
        "is_admin": is_admin,
        "exp": datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

async def get_current_user(request: Request) -> dict:
    """Get current authenticated user with role from database"""
    token = request.cookies.get("session_token")
    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
    
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user = await db.users.find_one({"user_id": payload["user_id"]}, {"_id": 0, "password": 0})
        if user:
            # ALWAYS get role from database, never from token
            user["is_admin"] = user.get("is_admin", False)
            return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        pass
    
    raise HTTPException(status_code=401, detail="Invalid token")

async def get_admin_user(request: Request) -> dict:
    """Get current admin user - requires admin role in DB"""
    user = await get_current_user(request)
    if not user.get("is_admin", False):
        raise HTTPException(status_code=403, detail="Admin access required")
    return user

def require_role(allowed_roles: list):
    """Dependency to require specific workspace roles"""
    async def check_role(user: dict = Depends(get_current_user)):
        # For admin endpoints, check is_admin flag
        if "admin" in allowed_roles and user.get("is_admin", False):
            return user
        # For workspace roles, check membership (handled separately)
        return user
    return check_role

async def get_workspace_member(workspace_id: str, user: dict) -> dict:
    """Check if user is member of workspace and return membership"""
    membership = await db.workspace_members.find_one({
        "workspace_id": workspace_id,
        "user_id": user["user_id"]
    }, {"_id": 0})
    
    if not membership:
        raise HTTPException(status_code=403, detail="Not a member of this workspace")
    
    return membership

# ==================== AUTH ROUTES ====================

@api_router.post("/auth/register")
async def register(user_data: UserCreate, request: Request, response: Response):
    # Rate limiting
    ip = security_service.get_client_ip(request)
    if security_service.rate_limiter.is_blocked(ip):
        raise HTTPException(status_code=429, detail="Too many requests. Try again later.")
    
    rate_check = security_service.rate_limiter.check_rate_limit("register", ip)
    if not rate_check["allowed"]:
        raise HTTPException(status_code=429, detail="Registration limit reached. Try again later.")
    
    existing = await db.users.find_one({"email": user_data.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    security_service.rate_limiter.record_request("register", ip)
    
    user_id = f"user_{uuid.uuid4().hex[:12]}"
    hashed_password = hash_password(user_data.password)
    
    # Create user
    user_doc = {
        "user_id": user_id,
        "email": user_data.email,
        "name": user_data.name,
        "password": hashed_password,
        "picture": None,
        "is_admin": user_data.email == ADMIN_EMAIL,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.users.insert_one(user_doc)
    
    # Create default workspace
    workspace_id = f"ws_{uuid.uuid4().hex[:12]}"
    workspace_doc = {
        "workspace_id": workspace_id,
        "name": f"{user_data.name}'s Workspace",
        "description": "Personal workspace",
        "owner_id": user_id,
        "plan": PlanType.FREE.value,
        "credits": 10,
        "features": [],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    await db.workspaces.insert_one(workspace_doc)
    
    # Add user as owner
    await db.workspace_members.insert_one({
        "workspace_id": workspace_id,
        "user_id": user_id,
        "role": UserRole.OWNER.value,
        "joined_at": datetime.now(timezone.utc).isoformat()
    })
    
    # Send webhook
    await webhook_service.user_registered(user_id, user_data.email, workspace_id)
    
    # Send welcome email
    await email_service.email_service.send_welcome_email(user_data.email, user_data.name)
    
    token = create_jwt_token(user_id, user_data.email, user_doc["is_admin"])
    response.set_cookie(
        key="session_token", value=token,
        httponly=True, secure=True, samesite="none",
        path="/", max_age=JWT_EXPIRATION_HOURS * 3600
    )
    
    return {
        "user_id": user_id,
        "email": user_data.email,
        "name": user_data.name,
        "is_admin": user_doc["is_admin"],
        "default_workspace_id": workspace_id,
        "token": token
    }

@api_router.post("/auth/login")
async def login(user_data: UserLogin, request: Request, response: Response):
    ip = security_service.get_client_ip(request)
    
    # Check if IP is blocked
    if security_service.rate_limiter.is_blocked(ip):
        raise HTTPException(status_code=429, detail="Too many failed attempts. Try again later.")
    
    # Rate limit check
    rate_check = security_service.rate_limiter.check_rate_limit("login", ip)
    if not rate_check["allowed"]:
        raise HTTPException(status_code=429, detail="Too many login attempts. Try again later.")
    
    user = await db.users.find_one({"email": user_data.email}, {"_id": 0})
    if not user or not verify_password(user_data.password, user.get("password", "")):
        # Record failed login
        security_service.rate_limiter.record_failed_login(ip)
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Clear failed attempts on success
    security_service.rate_limiter.clear_failed_logins(ip)
    security_service.rate_limiter.record_request("login", ip)
    
    token = create_jwt_token(user["user_id"], user["email"], user.get("is_admin", False))
    response.set_cookie(
        key="session_token", value=token,
        httponly=True, secure=True, samesite="none",
        path="/", max_age=JWT_EXPIRATION_HOURS * 3600
    )
    
    # Get default workspace
    membership = await db.workspace_members.find_one({"user_id": user["user_id"]}, {"_id": 0})
    
    return {
        "user_id": user["user_id"],
        "email": user["email"],
        "name": user["name"],
        "is_admin": user.get("is_admin", False),
        "default_workspace_id": membership["workspace_id"] if membership else None,
        "token": token
    }

@api_router.get("/auth/google/url")
async def get_google_auth_url(redirect_uri: str):
    if not GOOGLE_CLIENT_ID:
        raise HTTPException(status_code=500, detail="Google OAuth not configured")
    
    auth_url = (
        f"https://accounts.google.com/o/oauth2/v2/auth?"
        f"client_id={GOOGLE_CLIENT_ID}&"
        f"redirect_uri={redirect_uri}&"
        f"response_type=code&"
        f"scope=openid email profile&"
        f"access_type=offline&prompt=consent"
    )
    return {"url": auth_url}

@api_router.post("/auth/google/callback")
async def google_auth_callback(auth_data: GoogleAuthRequest, response: Response):
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        raise HTTPException(status_code=500, detail="Google OAuth not configured")
    
    async with httpx.AsyncClient() as http_client:
        token_response = await http_client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": auth_data.code,
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "redirect_uri": auth_data.redirect_uri,
                "grant_type": "authorization_code"
            }
        )
        
        if token_response.status_code != 200:
            raise HTTPException(status_code=401, detail="Failed to authenticate with Google")
        
        tokens = token_response.json()
        user_response = await http_client.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {tokens['access_token']}"}
        )
        
        if user_response.status_code != 200:
            raise HTTPException(status_code=401, detail="Failed to get user info")
        
        google_user = user_response.json()
    
    email = google_user["email"]
    name = google_user.get("name", email.split("@")[0])
    picture = google_user.get("picture")
    
    user = await db.users.find_one({"email": email}, {"_id": 0})
    
    if user:
        await db.users.update_one({"email": email}, {"$set": {"name": name, "picture": picture}})
        user_id = user["user_id"]
        is_admin = user.get("is_admin", False)
    else:
        user_id = f"user_{uuid.uuid4().hex[:12]}"
        user_doc = {
            "user_id": user_id,
            "email": email,
            "name": name,
            "picture": picture,
            "is_admin": email == ADMIN_EMAIL,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.users.insert_one(user_doc)
        is_admin = user_doc["is_admin"]
        
        # Create default workspace
        workspace_id = f"ws_{uuid.uuid4().hex[:12]}"
        await db.workspaces.insert_one({
            "workspace_id": workspace_id,
            "name": f"{name}'s Workspace",
            "description": "Personal workspace",
            "owner_id": user_id,
            "plan": PlanType.FREE.value,
            "credits": 10,
            "features": [],
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        })
        await db.workspace_members.insert_one({
            "workspace_id": workspace_id,
            "user_id": user_id,
            "role": UserRole.OWNER.value,
            "joined_at": datetime.now(timezone.utc).isoformat()
        })
        await webhook_service.user_registered(user_id, email, workspace_id)
    
    token = create_jwt_token(user_id, email, is_admin)
    response.set_cookie(
        key="session_token", value=token,
        httponly=True, secure=True, samesite="none",
        path="/", max_age=7 * 24 * 3600
    )
    
    membership = await db.workspace_members.find_one({"user_id": user_id}, {"_id": 0})
    
    return {
        "user_id": user_id,
        "email": email,
        "name": name,
        "picture": picture,
        "is_admin": is_admin,
        "default_workspace_id": membership["workspace_id"] if membership else None,
        "token": token
    }

@api_router.get("/auth/me")
async def get_me(user: dict = Depends(get_current_user)):
    # Get workspaces
    memberships = await db.workspace_members.find({"user_id": user["user_id"]}, {"_id": 0}).to_list(100)
    workspace_ids = [m["workspace_id"] for m in memberships]
    workspaces = await db.workspaces.find({"workspace_id": {"$in": workspace_ids}}, {"_id": 0}).to_list(100)
    
    # Get credits and plan from default workspace (first one owned)
    default_ws = next((w for w in workspaces if w.get("owner_id") == user["user_id"]), workspaces[0] if workspaces else None)
    
    return {
        **user,
        "is_admin": user.get("is_admin", False),
        "credits": default_ws.get("credits", 0) if default_ws else 0,
        "plan": default_ws.get("plan", "free") if default_ws else "free",
        "workspaces": [{"workspace_id": w["workspace_id"], "name": w["name"], "credits": w.get("credits", 0), "plan": w.get("plan", "free"), "role": next((m["role"] for m in memberships if m["workspace_id"] == w["workspace_id"]), "member")} for w in workspaces]
    }

@api_router.post("/auth/logout")
async def logout(response: Response, user: dict = Depends(get_current_user)):
    response.delete_cookie(key="session_token", path="/")
    return {"message": "Logged out"}

# ==================== WORKSPACE ROUTES ====================

@api_router.post("/workspaces")
async def create_workspace(ws_data: WorkspaceCreate, user: dict = Depends(get_current_user)):
    # Check workspace limit
    count = await db.workspace_members.count_documents({"user_id": user["user_id"], "role": UserRole.OWNER.value})
    # For now, allow unlimited - can add plan-based limits later
    
    workspace_id = f"ws_{uuid.uuid4().hex[:12]}"
    workspace_doc = {
        "workspace_id": workspace_id,
        "name": ws_data.name,
        "description": ws_data.description,
        "owner_id": user["user_id"],
        "plan": PlanType.FREE.value,
        "credits": 10,
        "features": [],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    await db.workspaces.insert_one(workspace_doc)
    
    await db.workspace_members.insert_one({
        "workspace_id": workspace_id,
        "user_id": user["user_id"],
        "role": UserRole.OWNER.value,
        "joined_at": datetime.now(timezone.utc).isoformat()
    })
    
    workspace_doc.pop("_id", None)
    return workspace_doc

@api_router.get("/workspaces")
async def list_workspaces(user: dict = Depends(get_current_user)):
    memberships = await db.workspace_members.find({"user_id": user["user_id"]}, {"_id": 0}).to_list(100)
    workspace_ids = [m["workspace_id"] for m in memberships]
    workspaces = await db.workspaces.find({"workspace_id": {"$in": workspace_ids}}, {"_id": 0}).to_list(100)
    
    result = []
    for ws in workspaces:
        membership = next((m for m in memberships if m["workspace_id"] == ws["workspace_id"]), None)
        ws["role"] = membership["role"] if membership else "member"
        result.append(ws)
    
    return result

@api_router.get("/workspaces/{workspace_id}")
async def get_workspace(workspace_id: str, user: dict = Depends(get_current_user)):
    await get_workspace_member(workspace_id, user)
    workspace = await db.workspaces.find_one({"workspace_id": workspace_id}, {"_id": 0})
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    return workspace

@api_router.get("/workspaces/{workspace_id}/members")
async def get_workspace_members(workspace_id: str, user: dict = Depends(get_current_user)):
    await get_workspace_member(workspace_id, user)
    memberships = await db.workspace_members.find({"workspace_id": workspace_id}, {"_id": 0}).to_list(100)
    
    result = []
    for m in memberships:
        member_user = await db.users.find_one({"user_id": m["user_id"]}, {"_id": 0, "password": 0})
        if member_user:
            result.append({
                "user_id": m["user_id"],
                "email": member_user["email"],
                "name": member_user["name"],
                "role": m["role"],
                "joined_at": m["joined_at"]
            })
    
    return result

@api_router.post("/workspaces/{workspace_id}/members")
async def invite_member(workspace_id: str, invite: WorkspaceInvite, user: dict = Depends(get_current_user)):
    membership = await get_workspace_member(workspace_id, user)
    if membership["role"] not in [UserRole.OWNER.value, UserRole.ADMIN.value]:
        raise HTTPException(status_code=403, detail="Only owners and admins can invite members")
    
    # Find user by email
    invite_user = await db.users.find_one({"email": invite.email}, {"_id": 0})
    if not invite_user:
        raise HTTPException(status_code=404, detail="User not found. They must register first.")
    
    # Check if already member
    existing = await db.workspace_members.find_one({"workspace_id": workspace_id, "user_id": invite_user["user_id"]})
    if existing:
        raise HTTPException(status_code=400, detail="User is already a member")
    
    await db.workspace_members.insert_one({
        "workspace_id": workspace_id,
        "user_id": invite_user["user_id"],
        "role": invite.role.value,
        "joined_at": datetime.now(timezone.utc).isoformat()
    })
    
    return {"message": "Member added", "user_id": invite_user["user_id"]}

# ==================== PRODUCT ROUTES ====================

@api_router.post("/workspaces/{workspace_id}/products/generate")
async def generate_product(workspace_id: str, product_data: ProductCreate, user: dict = Depends(get_current_user)):
    membership = await get_workspace_member(workspace_id, user)
    workspace = await db.workspaces.find_one({"workspace_id": workspace_id}, {"_id": 0})
    
    if workspace.get("credits", 0) < 5:
        raise HTTPException(
            status_code=402,
            detail=f"Créditos insuficientes. Necessário: 5, Disponível: {workspace.get('credits', 0)}"
        )
    
    # Anti-abuse check
    abuse_check = security_service.credit_protection.check_credit_abuse(user["user_id"])
    if not abuse_check["allowed"]:
        raise HTTPException(status_code=429, detail=abuse_check["reason"])
    
    # Check LLM availability
    if not await llm_service.is_available():
        raise HTTPException(status_code=503, detail="LLM service not available")
    
    # Build prompt
    type_prompts = {
        "ebook": f"Cria um eBook completo sobre \"{product_data.topic}\" para {product_data.target_audience}.",
        "guide": f"Cria um guia prático sobre \"{product_data.topic}\" para {product_data.target_audience}.",
        "course": f"Cria um outline de curso sobre \"{product_data.topic}\" para {product_data.target_audience}.",
        "template": f"Cria um template profissional sobre \"{product_data.topic}\" para {product_data.target_audience}."
    }
    
    base_prompt = type_prompts.get(product_data.product_type, type_prompts["guide"])
    prompt = f"""{base_prompt}

Tom: {product_data.tone}
Idioma: {product_data.language}

Estrutura o conteúdo de forma profissional com:
- Título e introdução
- Secções principais detalhadas
- Conclusão com chamada à ação

Formata em Markdown."""
    
    # Get RAG context if available
    rag_docs = await rag_client.retrieve(f"{product_data.topic} {product_data.target_audience}")
    if rag_docs:
        rag_context = rag_client.format_context(rag_docs)
        prompt = f"{rag_context}\n\n{prompt}"
    
    system_message = "És um especialista em criação de produtos digitais premium. Crias conteúdo detalhado e profissional."
    
    try:
        content = await llm_service.generate(prompt, system_message)
        
        product_id = f"prod_{uuid.uuid4().hex[:12]}"
        now = datetime.now(timezone.utc).isoformat()
        
        product_doc = {
            "product_id": product_id,
            "workspace_id": workspace_id,
            "user_id": user["user_id"],
            "title": product_data.title,
            "description": product_data.description,
            "product_type": product_data.product_type,
            "topic": product_data.topic,
            "target_audience": product_data.target_audience,
            "tone": product_data.tone,
            "language": product_data.language,
            "content": content,
            "price": 0.0,
            "is_published": False,
            "landing_page": None,
            "downloads": 0,
            "revenue": 0.0,
            "views": 0,
            "created_at": now,
            "updated_at": now
        }
        
        await db.products.insert_one(product_doc)
        
        # Deduct 5 credits per generation
        await db.workspaces.update_one({"workspace_id": workspace_id}, {"$inc": {"credits": -5}})
        
        # Record usage for anti-abuse
        security_service.credit_protection.record_credit_usage(user["user_id"], 5)
        
        # Record usage
        await db.usage.insert_one({
            "workspace_id": workspace_id,
            "user_id": user["user_id"],
            "action": "generation",
            "credits_used": 5,
            "metadata": {"product_id": product_id, "type": product_data.product_type},
            "created_at": now
        })
        
        product_doc.pop("_id", None)
        return product_doc
        
    except Exception as e:
        logger.error(f"Product generation error: {e}")
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")

@api_router.get("/workspaces/{workspace_id}/products")
async def list_products(workspace_id: str, user: dict = Depends(get_current_user)):
    await get_workspace_member(workspace_id, user)
    products = await db.products.find({"workspace_id": workspace_id}, {"_id": 0}).sort("created_at", -1).to_list(100)
    return products

@api_router.get("/workspaces/{workspace_id}/products/{product_id}")
async def get_product(workspace_id: str, product_id: str, user: dict = Depends(get_current_user)):
    await get_workspace_member(workspace_id, user)
    product = await db.products.find_one({"product_id": product_id, "workspace_id": workspace_id}, {"_id": 0})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@api_router.put("/workspaces/{workspace_id}/products/{product_id}")
async def update_product(workspace_id: str, product_id: str, update_data: ProductUpdate, user: dict = Depends(get_current_user)):
    await get_workspace_member(workspace_id, user)
    
    # Get existing product
    product = await db.products.find_one({"product_id": product_id, "workspace_id": workspace_id}, {"_id": 0})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    update_dict = {k: v for k, v in update_data.model_dump().items() if v is not None}
    update_dict["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    # Handle publication with slug
    if "status" in update_dict:
        update_dict["is_published"] = (update_dict["status"] == "published")
        
        if update_dict["is_published"] and not product.get("slug"):
            # Generate unique slug
            base_slug = generate_slug(product["title"])
            slug = base_slug
            counter = 1
            
            while await db.products.find_one({"slug": slug, "product_id": {"$ne": product_id}}):
                slug = f"{base_slug}-{counter}"
                counter += 1
            
            update_dict["slug"] = slug
            update_dict["public_url"] = f"/p/{slug}"
    
    result = await db.products.update_one(
        {"product_id": product_id, "workspace_id": workspace_id},
        {"$set": update_dict}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Product not found")
    
    return await db.products.find_one({"product_id": product_id}, {"_id": 0})

@api_router.delete("/workspaces/{workspace_id}/products/{product_id}")
async def delete_product(workspace_id: str, product_id: str, user: dict = Depends(get_current_user)):
    membership = await get_workspace_member(workspace_id, user)
    if membership["role"] not in [UserRole.OWNER.value, UserRole.ADMIN.value]:
        raise HTTPException(status_code=403, detail="Only owners and admins can delete products")
    
    result = await db.products.delete_one({"product_id": product_id, "workspace_id": workspace_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Product not found")
    
    return {"message": "Product deleted"}

# ==================== CAMPAIGN BUILDER ROUTES ====================

@api_router.post("/workspaces/{workspace_id}/campaigns/generate")
async def generate_campaign(workspace_id: str, campaign_data: CampaignCreate, user: dict = Depends(get_current_user)):
    membership = await get_workspace_member(workspace_id, user)
    workspace = await db.workspaces.find_one({"workspace_id": workspace_id}, {"_id": 0})
    
    if workspace.get("credits", 0) < 3:  # Campaigns cost 3 credits
        raise HTTPException(status_code=402, detail="Insufficient credits (campaigns require 3 credits)")
    
    if not await llm_service.is_available():
        raise HTTPException(status_code=503, detail="LLM service not available")
    
    try:
        campaign = await campaign_builder.generate_campaign(
            niche=campaign_data.niche,
            product=campaign_data.product,
            offer=campaign_data.offer,
            price=campaign_data.price,
            objective=campaign_data.objective,
            tone=campaign_data.tone,
            channel=campaign_data.channel,
            language=campaign_data.language,
            use_rag=campaign_data.use_rag
        )
        
        # Add workspace info
        campaign["workspace_id"] = workspace_id
        campaign["user_id"] = user["user_id"]
        
        # Save to database (exclude _id to let MongoDB generate it)
        campaign_doc = {k: v for k, v in campaign.items() if k != "_id"}
        await db.campaigns.insert_one(campaign_doc)
        
        # Deduct credits
        await db.workspaces.update_one({"workspace_id": workspace_id}, {"$inc": {"credits": -3}})
        
        # Record usage
        await db.usage.insert_one({
            "workspace_id": workspace_id,
            "user_id": user["user_id"],
            "action": "campaign_generation",
            "credits_used": 3,
            "metadata": {"campaign_id": campaign["campaign_id"]},
            "created_at": campaign["created_at"]
        })
        
        # Send webhook
        await webhook_service.campaign_created(campaign["campaign_id"], workspace_id, user["user_id"], campaign_data.channel)
        
        return campaign
        
    except Exception as e:
        logger.error(f"Campaign generation error: {e}")
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")

@api_router.get("/workspaces/{workspace_id}/campaigns")
async def list_campaigns(workspace_id: str, user: dict = Depends(get_current_user)):
    await get_workspace_member(workspace_id, user)
    campaigns = await db.campaigns.find({"workspace_id": workspace_id}, {"_id": 0}).sort("created_at", -1).to_list(100)
    return campaigns

@api_router.get("/workspaces/{workspace_id}/campaigns/{campaign_id}")
async def get_campaign(workspace_id: str, campaign_id: str, user: dict = Depends(get_current_user)):
    await get_workspace_member(workspace_id, user)
    campaign = await db.campaigns.find_one({"campaign_id": campaign_id, "workspace_id": workspace_id}, {"_id": 0})
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return campaign

@api_router.get("/workspaces/{workspace_id}/campaigns/{campaign_id}/export")
async def export_campaign(workspace_id: str, campaign_id: str, user: dict = Depends(get_current_user)):
    await get_workspace_member(workspace_id, user)
    campaign = await db.campaigns.find_one({"campaign_id": campaign_id, "workspace_id": workspace_id}, {"_id": 0})
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    try:
        zip_bytes = campaign_builder.create_zip(campaign)
        
        # Record export
        await db.usage.insert_one({
            "workspace_id": workspace_id,
            "user_id": user["user_id"],
            "action": "export",
            "credits_used": 0,
            "metadata": {"campaign_id": campaign_id, "type": "zip"},
            "created_at": datetime.now(timezone.utc).isoformat()
        })
        
        # Send webhook  
        try:
            await webhook_service.export_generated(
                f"exp_{uuid.uuid4().hex[:8]}", workspace_id, user["user_id"], "campaign_zip", len(zip_bytes)
            )
        except:
            pass  # Webhook is optional
        
        return StreamingResponse(
            io.BytesIO(zip_bytes),
            media_type="application/zip",
            headers={"Content-Disposition": f"attachment; filename=campaign_{campaign_id}.zip"}
        )
        
    except Exception as e:
        logger.error(f"Export error: {e}")
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")

# ==================== PUBLIC ROUTES ====================

@api_router.get("/public/products")
async def get_public_products(skip: int = 0, limit: int = 50, product_type: Optional[str] = None):
    """Get all published products for public catalog"""
    query = {"is_published": True}
    
    if product_type:
        query["product_type"] = product_type
    
    products = await db.products.find(
        query,
        {"_id": 0, "content": 0, "workspace_id": 0, "user_id": 0}  # Hide sensitive data
    ).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
    
    total = await db.products.count_documents(query)
    
    return {
        "products": products,
        "total": total,
        "skip": skip,
        "limit": limit
    }

@api_router.get("/public/product/slug/{slug}")
async def get_public_product_by_slug(slug: str):
    """Get published product by slug for public viewing"""
    product = await db.products.find_one({
        "slug": slug,
        "is_published": True
    }, {"_id": 0, "workspace_id": 0, "user_id": 0})
    
    if not product:
        raise HTTPException(status_code=404, detail="Produto não encontrado ou não publicado")
    
    # Increment views
    await db.products.update_one(
        {"slug": slug},
        {"$inc": {"views": 1}}
    )
    
    return product


# ==================== PUBLIC ROUTES ====================

@api_router.get("/public/product/{product_id}")
async def get_public_product(product_id: str):
    product = await db.products.find_one({"product_id": product_id, "is_published": True}, {"_id": 0, "content": 0})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    await db.products.update_one({"product_id": product_id}, {"$inc": {"views": 1}})
    return product


# ==================== PURCHASE ROUTES ====================

@api_router.post("/products/{product_id}/purchase")
async def create_product_purchase(product_id: str, request: Request, user: dict = Depends(get_current_user)):
    """Create Stripe checkout session for product purchase"""
    # Get product
    product = await db.products.find_one({
        "product_id": product_id,
        "is_published": True
    }, {"_id": 0})
    
    if not product:
        raise HTTPException(status_code=404, detail="Produto não encontrado ou não publicado")
    
    if product.get("price", 0) <= 0:
        raise HTTPException(status_code=400, detail="Produto gratuito não requer pagamento")
    
    # Check if already purchased
    existing = await db.purchases.find_one({
        "user_id": user["user_id"],
        "product_id": product_id,
        "status": "completed"
    })
    
    if existing:
        raise HTTPException(status_code=400, detail="Já adquiriste este produto")
    
    # Create purchase record
    purchase_id = f"purchase_{uuid.uuid4().hex[:16]}"
    purchase = {
        "purchase_id": purchase_id,
        "user_id": user["user_id"],
        "product_id": product_id,
        "workspace_id": product["workspace_id"],
        "amount": product["price"],
        "payment_method": "stripe",
        "status": "pending",
        "purchased_at": datetime.now(timezone.utc).isoformat(),
        "access_granted": False
    }
    await db.purchases.insert_one(purchase)
    
    # Create Stripe session
    data = await request.json()
    origin_url = data.get("origin_url", "")
    
    try:
        session = await payment_service.create_stripe_checkout(
            user_id=user["user_id"],
            plan_name=product["title"],
            price=product["price"],
            credits=0,
            mode="payment",
            success_url=f"{origin_url}/purchase/success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{origin_url}/p/{product_id}",
            metadata={"purchase_id": purchase_id, "product_id": product_id}
        )
        
        # Update purchase with session_id
        await db.purchases.update_one(
            {"purchase_id": purchase_id},
            {"$set": {"stripe_session_id": session["id"]}}
        )
        
        return {"checkout_url": session["url"]}
    except Exception as e:
        logger.error(f"Stripe checkout error: {e}")
        raise HTTPException(status_code=500, detail="Erro ao criar checkout")

@api_router.get("/purchases/verify")
async def verify_purchase(session_id: str, user: dict = Depends(get_current_user)):
    """Verify Stripe payment and grant access"""
    try:
        # Get Stripe session
        session_data = await payment_service.get_stripe_session(session_id)
        
        if session_data["status"] != "paid":
            return {"status": "pending", "message": "Pagamento pendente"}
        
        # Find purchase
        purchase = await db.purchases.find_one({
            "stripe_session_id": session_id,
            "user_id": user["user_id"]
        })
        
        if not purchase:
            raise HTTPException(status_code=404, detail="Compra não encontrada")
        
        # Grant access if not already granted
        if not purchase.get("access_granted"):
            await db.purchases.update_one(
                {"purchase_id": purchase["purchase_id"]},
                {"$set": {
                    "status": "completed",
                    "access_granted": True,
                    "completed_at": datetime.now(timezone.utc).isoformat()
                }}
            )
            
            # Update product stats
            await db.products.update_one(
                {"product_id": purchase["product_id"]},
                {"$inc": {"downloads": 1, "revenue": purchase["amount"]}}
            )
        
        # Get product
        product = await db.products.find_one(
            {"product_id": purchase["product_id"]},
            {"_id": 0}
        )
        
        return {
            "status": "completed",
            "message": "Acesso garantido",
            "product": product,
            "download_url": product.get("content") if product else None
        }
        
    except Exception as e:
        logger.error(f"Purchase verification error: {e}")
        raise HTTPException(status_code=500, detail="Erro ao verificar compra")

@api_router.get("/purchases/my")
async def get_my_purchases(user: dict = Depends(get_current_user)):
    """Get user's purchases"""
    purchases = await db.purchases.find(
        {"user_id": user["user_id"], "status": "completed"},
        {"_id": 0}
    ).sort("purchased_at", -1).to_list(100)
    
    # Enrich with product data
    for purchase in purchases:
        product = await db.products.find_one(
            {"product_id": purchase["product_id"]},
            {"_id": 0, "title": 1, "product_type": 1}
        )
        if product:
            purchase["product_title"] = product.get("title")
            purchase["product_type"] = product.get("product_type")
    
    return purchases


# ==================== BILLING ROUTES ====================

@api_router.get("/billing/plans")
async def get_billing_plans():
    """Get available plans with payment status"""
    payment_status = payment_service.get_status()
    return {
        "plans": {k.value: {**v, "plan_id": k.value} for k, v in DEFAULT_PLANS.items()},
        "stripe_enabled": payment_status["stripe_enabled"],
        "paypal_enabled": payment_status["paypal_enabled"]
    }

@api_router.post("/billing/checkout/stripe")
async def create_stripe_checkout(request: Request, user: dict = Depends(get_current_user)):
    """Create Stripe checkout session"""
    data = await request.json()
    plan_id = data.get("plan_id")
    origin_url = data.get("origin_url", "")
    
    plan_enum = PlanType(plan_id) if plan_id in [p.value for p in PlanType] else None
    if not plan_enum:
        raise HTTPException(status_code=400, detail="Invalid plan")
    
    plan = DEFAULT_PLANS.get(plan_enum)
    if not plan or plan["price"] == 0:
        raise HTTPException(status_code=400, detail="Cannot checkout free plan")
    
    try:
        result = await payment_service.payment_service.create_stripe_checkout(
            user_id=user["user_id"],
            email=user["email"],
            plan_id=plan_id,
            plan_name=plan["name"],
            price=plan["price"],
            credits=plan["credits_monthly"],
            success_url=f"{origin_url}/settings?payment=success",
            cancel_url=f"{origin_url}/settings?payment=cancelled"
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@api_router.post("/billing/checkout/paypal")
async def create_paypal_checkout(request: Request, user: dict = Depends(get_current_user)):
    """Create PayPal order"""
    data = await request.json()
    plan_id = data.get("plan_id")
    origin_url = data.get("origin_url", "")
    
    plan_enum = PlanType(plan_id) if plan_id in [p.value for p in PlanType] else None
    if not plan_enum:
        raise HTTPException(status_code=400, detail="Invalid plan")
    
    plan = DEFAULT_PLANS.get(plan_enum)
    if not plan or plan["price"] == 0:
        raise HTTPException(status_code=400, detail="Cannot checkout free plan")
    
    try:
        result = await payment_service.payment_service.create_paypal_order(
            user_id=user["user_id"],
            plan_id=plan_id,
            plan_name=plan["name"],
            price=plan["price"],
            credits=plan["credits_monthly"],
            return_url=f"{origin_url}/settings?payment=success",
            cancel_url=f"{origin_url}/settings?payment=cancelled"
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@api_router.post("/billing/confirm/stripe")
async def confirm_stripe_payment(request: Request, user: dict = Depends(get_current_user)):
    """Confirm Stripe payment and activate plan"""
    data = await request.json()
    session_id = data.get("session_id")
    
    if not session_id:
        raise HTTPException(status_code=400, detail="Session ID required")
    
    try:
        session = await payment_service.payment_service.get_stripe_session(session_id)
        
        if session["status"] != "paid":
            raise HTTPException(status_code=400, detail="Payment not completed")
        
        # Check if already processed
        existing = await db.payments.find_one({"provider_id": session_id})
        if existing:
            return {"status": "already_processed", "credits": existing.get("credits", 0)}
        
        # Get plan details from metadata
        metadata = session.get("metadata", {})
        plan_id = metadata.get("plan_id", "starter")
        credits = int(metadata.get("credits", 50))
        
        # Activate plan
        membership = await db.workspace_members.find_one({"user_id": user["user_id"]})
        if membership:
            await db.workspaces.update_one(
                {"workspace_id": membership["workspace_id"]},
                {"$set": {"plan": plan_id}, "$inc": {"credits": credits}}
            )
        
        # Record payment
        payment_record = {
            "payment_id": f"pay_{uuid.uuid4().hex[:12]}",
            "provider": "stripe",
            "provider_id": session_id,
            "user_id": user["user_id"],
            "workspace_id": membership["workspace_id"] if membership else None,
            "plan_id": plan_id,
            "amount": session.get("amount_total", 0),
            "credits": credits,
            "status": "completed",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.payments.insert_one(payment_record)
        
        # Send confirmation email
        plan_name = DEFAULT_PLANS.get(PlanType(plan_id), {}).get("name", plan_id)
        await email_service.email_service.send_payment_success_email(
            user["email"], user["name"], plan_name,
            session.get("amount_total", 0), credits, session_id
        )
        
        return {"status": "success", "credits": credits, "plan": plan_id}
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@api_router.post("/billing/confirm/paypal")
async def confirm_paypal_payment(request: Request, user: dict = Depends(get_current_user)):
    """Confirm PayPal payment and activate plan"""
    data = await request.json()
    order_id = data.get("order_id")
    
    if not order_id:
        raise HTTPException(status_code=400, detail="Order ID required")
    
    try:
        # Check if already processed
        existing = await db.payments.find_one({"provider_id": order_id})
        if existing:
            return {"status": "already_processed", "credits": existing.get("credits", 0)}
        
        # Capture the payment
        capture_result = await payment_service.payment_service.capture_paypal_order(order_id)
        
        if capture_result["status"] != "COMPLETED":
            raise HTTPException(status_code=400, detail="Payment not completed")
        
        user_id = capture_result.get("user_id", user["user_id"])
        plan_id = capture_result.get("plan_id", "starter")
        credits = capture_result.get("credits", 50)
        amount = capture_result.get("amount", 0)
        
        # Activate plan
        membership = await db.workspace_members.find_one({"user_id": user_id})
        if membership:
            await db.workspaces.update_one(
                {"workspace_id": membership["workspace_id"]},
                {"$set": {"plan": plan_id}, "$inc": {"credits": credits}}
            )
        
        # Record payment
        payment_record = {
            "payment_id": f"pay_{uuid.uuid4().hex[:12]}",
            "provider": "paypal",
            "provider_id": order_id,
            "user_id": user_id,
            "workspace_id": membership["workspace_id"] if membership else None,
            "plan_id": plan_id,
            "amount": amount,
            "credits": credits,
            "status": "completed",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.payments.insert_one(payment_record)
        
        # Send confirmation email
        plan_name = DEFAULT_PLANS.get(PlanType(plan_id), {}).get("name", plan_id)
        await email_service.email_service.send_payment_success_email(
            user["email"], user["name"], plan_name,
            amount, credits, order_id
        )
        
        return {"status": "success", "credits": credits, "plan": plan_id}
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@api_router.post("/billing/webhook/stripe")
async def stripe_webhook(request: Request):
    """Handle Stripe webhooks with idempotency"""
    payload = await request.body()
    signature = request.headers.get("stripe-signature", "")
    
    try:
        event = payment_service.payment_service.verify_stripe_webhook(payload, signature)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid signature")
    
    event_id = event.get("id")
    event_type = event["type"]
    
    # Check idempotency - prevent duplicate processing
    existing_event = await db.webhook_events.find_one({"event_id": event_id})
    if existing_event:
        logger.info(f"Webhook event {event_id} already processed, skipping")
        return {"status": "already_processed", "event_id": event_id}
    
    # Record event
    await db.webhook_events.insert_one({
        "event_id": event_id,
        "event_type": event_type,
        "processed_at": datetime.now(timezone.utc).isoformat(),
        "payload_summary": {
            "type": event_type,
            "created": event.get("created")
        }
    })
    
    # Handle checkout.session.completed
    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        metadata = session.get("metadata", {})
        
        user_id = metadata.get("user_id")
        plan_id = metadata.get("plan_id", "starter")
        credits = int(metadata.get("credits", 50))
        
        if user_id:
            # Check if already processed
            existing = await db.payments.find_one({"provider_id": session["id"]})
            if not existing:
                # Activate plan
                membership = await db.workspace_members.find_one({"user_id": user_id})
                if membership:
                    await db.workspaces.update_one(
                        {"workspace_id": membership["workspace_id"]},
                        {"$set": {"plan": plan_id}, "$inc": {"credits": credits}}
                    )
                
                # Record payment
                await db.payments.insert_one({
                    "payment_id": f"pay_{uuid.uuid4().hex[:12]}",
                    "provider": "stripe",
                    "provider_id": session["id"],
                    "user_id": user_id,
                    "workspace_id": membership["workspace_id"] if membership else None,
                    "plan_id": plan_id,
                    "amount": session.get("amount_total", 0) / 100,
                    "credits": credits,
                    "status": "completed",
                    "webhook": True,
                    "created_at": datetime.now(timezone.utc).isoformat()
                })
                
                # Send email
                user = await db.users.find_one({"user_id": user_id})
                if user:
                    plan_name = DEFAULT_PLANS.get(PlanType(plan_id), {}).get("name", plan_id)
                    await email_service.email_service.send_payment_success_email(
                        user["email"], user["name"], plan_name,
                        session.get("amount_total", 0) / 100, credits, session["id"]
                    )
    
    return {"received": True}

@api_router.get("/billing/history")
async def get_payment_history(user: dict = Depends(get_current_user)):
    """Get user payment history"""
    payments = await db.payments.find(
        {"user_id": user["user_id"]},
        {"_id": 0}
    ).sort("created_at", -1).limit(50).to_list(50)
    return payments

# ==================== PASSWORD RESET ====================

@api_router.post("/auth/forgot-password")
async def forgot_password(request: Request):
    """Request password reset"""
    data = await request.json()
    email = data.get("email")
    
    if not email:
        raise HTTPException(status_code=400, detail="Email required")
    
    # Rate limit
    ip = security_service.get_client_ip(request)
    rate_check = security_service.rate_limiter.check_rate_limit("password_reset", ip)
    if not rate_check["allowed"]:
        raise HTTPException(status_code=429, detail="Too many reset requests. Try again later.")
    security_service.rate_limiter.record_request("password_reset", ip)
    
    user = await db.users.find_one({"email": email})
    
    # Always return success to prevent email enumeration
    if user:
        token = email_service.generate_reset_token()
        expiry = email_service.token_expiry()
        
        # Store reset token
        await db.password_resets.update_one(
            {"user_id": user["user_id"]},
            {"$set": {
                "token": token,
                "expires_at": expiry,
                "created_at": datetime.now(timezone.utc).isoformat()
            }},
            upsert=True
        )
        
        # Send email
        await email_service.email_service.send_password_reset_email(
            user["email"], user["name"], token
        )
    
    return {"message": "If an account exists with this email, you will receive a reset link."}

@api_router.post("/auth/reset-password")
async def reset_password(request: Request):
    """Reset password with token"""
    data = await request.json()
    token = data.get("token")
    new_password = data.get("password")
    
    if not token or not new_password:
        raise HTTPException(status_code=400, detail="Token and password required")
    
    if len(new_password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")
    
    # Find valid token
    reset_record = await db.password_resets.find_one({"token": token})
    if not reset_record:
        raise HTTPException(status_code=400, detail="Invalid or expired token")
    
    # Check expiry
    if datetime.fromisoformat(reset_record["expires_at"]) < datetime.now(timezone.utc):
        await db.password_resets.delete_one({"token": token})
        raise HTTPException(status_code=400, detail="Token expired")
    
    # Update password
    hashed = hash_password(new_password)
    await db.users.update_one(
        {"user_id": reset_record["user_id"]},
        {"$set": {"password": hashed}}
    )
    
    # Delete used token
    await db.password_resets.delete_one({"token": token})
    
    return {"message": "Password updated successfully"}

# ==================== ADMIN ROUTES ====================


@admin_router.get("/stats")
async def get_admin_stats(user: dict = Depends(get_admin_user)):
    total_users = await db.users.count_documents({})
    total_workspaces = await db.workspaces.count_documents({})
    total_products = await db.products.count_documents({})
    total_campaigns = await db.campaigns.count_documents({})
    
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    this_month = datetime.now(timezone.utc).strftime("%Y-%m")
    
    usage_today = await db.usage.count_documents({"created_at": {"$regex": f"^{today}"}})
    usage_month = await db.usage.count_documents({"created_at": {"$regex": f"^{this_month}"}})
    
    total_generations = await db.usage.count_documents({"action": {"$in": ["generation", "campaign_generation"]}})
    total_exports = await db.usage.count_documents({"action": "export"})
    
    llm_status = llm_service.get_status()
    rag_status = rag_client.get_status()
    
    return {
        "total_users": total_users,
        "total_workspaces": total_workspaces,
        "total_products": total_products,
        "total_campaigns": total_campaigns,
        "total_generations": total_generations,
        "total_exports": total_exports,
        "active_subscriptions": 0,  # TODO: implement
        "revenue_total": 0.0,  # TODO: implement
        "usage_today": usage_today,
        "usage_month": usage_month,
        "llm_provider": llm_status["provider"],
        "rag_enabled": rag_status["enabled"],
        "stripe_enabled": STRIPE_ENABLED
    }

@admin_router.get("/users")
async def list_users(page: int = 1, per_page: int = 20, user: dict = Depends(get_admin_user)):
    skip = (page - 1) * per_page
    users = await db.users.find({}, {"_id": 0, "password": 0}).skip(skip).limit(per_page).to_list(per_page)
    total = await db.users.count_documents({})
    
    return {"users": users, "total": total, "page": page, "per_page": per_page}

@admin_router.get("/templates")
async def list_templates(user: dict = Depends(get_admin_user)):
    templates = await db.templates.find({}, {"_id": 0}).sort("created_at", -1).to_list(100)
    return templates

@admin_router.post("/templates")
async def create_template(template_data: TemplateCreate, user: dict = Depends(get_admin_user)):
    template_id = f"tpl_{uuid.uuid4().hex[:12]}"
    now = datetime.now(timezone.utc).isoformat()
    
    template_doc = {
        "template_id": template_id,
        "name": template_data.name,
        "description": template_data.description,
        "type": template_data.type,
        "content": template_data.content,
        "created_at": now,
        "updated_at": now
    }
    
    await db.templates.insert_one(template_doc)
    return TemplateResponse(**template_doc)

# ==================== MEDIA ASSET ROUTES (ADMIN) ====================

@admin_router.post("/media/upload")
async def upload_media(
    file: UploadFile = File(...),
    admin: dict = Depends(get_admin_user)
):
    """Upload media asset - Admin only"""
    # Validate file size
    contents = await file.read()
    file_size = len(contents)
    
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"Ficheiro demasiado grande. Máximo: {MAX_FILE_SIZE / 1024 / 1024}MB"
        )
    
    # Validate MIME type
    mime_type = file.content_type
    if mime_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Tipo de ficheiro não suportado. Tipos permitidos: imagens, vídeos, PDFs"
        )
    
    try:
        # Generate secure filename
        secure_filename = generate_secure_filename(file.filename)
        file_path = UPLOAD_DIR / secure_filename
        
        # Save file
        with open(file_path, "wb") as f:
            f.write(contents)
        
        # Get workspace for admin
        membership = await db.workspace_members.find_one({"user_id": admin["user_id"]})
        workspace_id = membership["workspace_id"] if membership else None
        
        # Create database record
        asset_id = f"asset_{uuid.uuid4().hex[:16]}"
        asset_type = get_asset_type(mime_type)
        
        asset = {
            "asset_id": asset_id,
            "workspace_id": workspace_id,
            "owner_id": admin["user_id"],
            "filename": secure_filename,
            "original_filename": file.filename,
            "type": asset_type.value,
            "size": file_size,
            "mime_type": mime_type,
            "url": f"/uploads/{secure_filename}",
            "secure_url": f"/api/media/{asset_id}",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        await db.media_assets.insert_one(asset)
        
        logger.info(f"Media uploaded: {asset_id} by {admin['user_id']}")
        
        return MediaAssetResponse(**asset)
        
    except Exception as e:
        # Cleanup file on error
        if file_path.exists():
            file_path.unlink()
        logger.error(f"Upload error: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao fazer upload: {str(e)}")

@admin_router.get("/media")
async def list_media(
    admin: dict = Depends(get_admin_user),
    skip: int = 0,
    limit: int = 100,
    type: Optional[MediaAssetType] = None
):
    """List media assets - Admin only"""
    query = {}
    
    if type:
        query["type"] = type.value
    
    assets = await db.media_assets.find(query, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
    total = await db.media_assets.count_documents(query)
    
    return {
        "assets": assets,
        "total": total,
        "skip": skip,
        "limit": limit
    }

@admin_router.delete("/media/{asset_id}")
async def delete_media(asset_id: str, admin: dict = Depends(get_admin_user)):
    """Delete media asset - Admin only"""
    asset = await db.media_assets.find_one({"asset_id": asset_id})
    
    if not asset:
        raise HTTPException(status_code=404, detail="Asset não encontrado")
    
    # Delete file
    file_path = UPLOAD_DIR / asset["filename"]
    if file_path.exists():
        file_path.unlink()
    
    # Delete database record
    await db.media_assets.delete_one({"asset_id": asset_id})
    
    logger.info(f"Media deleted: {asset_id} by {admin['user_id']}")
    
    return {"status": "deleted", "asset_id": asset_id}

@api_router.get("/media/{asset_id}")
async def serve_media(asset_id: str, user: dict = Depends(get_current_user)):
    """Serve media file - Requires authentication"""
    asset = await db.media_assets.find_one({"asset_id": asset_id})
    
    if not asset:
        raise HTTPException(status_code=404, detail="Asset não encontrado")
    
    file_path = UPLOAD_DIR / asset["filename"]
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Ficheiro não encontrado")
    
    return FileResponse(
        file_path,
        media_type=asset["mime_type"],
        filename=asset["original_filename"]
    )


@admin_router.put("/templates/{template_id}")
async def update_template(template_id: str, update_data: TemplateUpdate, user: dict = Depends(get_admin_user)):
    update_dict = {k: v for k, v in update_data.model_dump().items() if v is not None}
    update_dict["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    result = await db.templates.update_one({"template_id": template_id}, {"$set": update_dict})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Template not found")
    
    return await db.templates.find_one({"template_id": template_id}, {"_id": 0})

@admin_router.delete("/templates/{template_id}")
async def delete_template(template_id: str, user: dict = Depends(get_admin_user)):
    result = await db.templates.delete_one({"template_id": template_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Template not found")
    return {"message": "Template deleted"}

@admin_router.get("/plans")
async def get_plans_config(user: dict = Depends(get_admin_user)):
    # Get from database or return defaults
    plans = await db.plans.find({}, {"_id": 0}).to_list(10)
    if not plans:
        return {k.value: v for k, v in DEFAULT_PLANS.items()}
    return {p["plan_id"]: p for p in plans}

@admin_router.put("/plans/{plan_id}")
async def update_plan(plan_id: str, update_data: PlanUpdate, user: dict = Depends(get_admin_user)):
    update_dict = {k: v for k, v in update_data.model_dump().items() if v is not None}
    update_dict["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    await db.plans.update_one(
        {"plan_id": plan_id},
        {"$set": update_dict},
        upsert=True
    )
    
    return await db.plans.find_one({"plan_id": plan_id}, {"_id": 0})

# ==================== SYSTEM STATUS ====================

@api_router.get("/status")
async def get_system_status():
    llm_status = llm_service.get_status()
    rag_status = rag_client.get_status()
    webhook_status = webhook_service.get_status()
    
    # Test database
    db_connected = True
    try:
        await db.command("ping")
    except Exception:
        db_connected = False
    
    return {
        "version": "2.0.0",
        "llm_provider": llm_status["provider"],
        "llm_available": await llm_service.is_available(),
        "rag_enabled": rag_status["enabled"],
        "rag_available": await rag_client.is_available() if rag_status["enabled"] else False,
        "stripe_enabled": STRIPE_ENABLED,
        "webhooks_enabled": webhook_status["enabled"],
        "database_connected": db_connected
    }

# ==================== LEGACY COMPATIBILITY ====================
# Keep old routes working for existing frontend

@api_router.get("/products")
async def legacy_list_products(user: dict = Depends(get_current_user)):
    """Legacy: list products from default workspace"""
    membership = await db.workspace_members.find_one({"user_id": user["user_id"]}, {"_id": 0})
    if not membership:
        return []
    products = await db.products.find({"workspace_id": membership["workspace_id"]}, {"_id": 0}).sort("created_at", -1).to_list(100)
    return products

@api_router.post("/products/generate")
async def legacy_generate_product(product_data: ProductCreate, user: dict = Depends(get_current_user)):
    """Legacy: generate product in default workspace"""
    membership = await db.workspace_members.find_one({"user_id": user["user_id"]}, {"_id": 0})
    if not membership:
        raise HTTPException(status_code=400, detail="No workspace found")
    return await generate_product(membership["workspace_id"], product_data, user)

@api_router.get("/analytics")
async def legacy_analytics(user: dict = Depends(get_current_user)):
    """Legacy: analytics for default workspace"""
    membership = await db.workspace_members.find_one({"user_id": user["user_id"]}, {"_id": 0})
    if not membership:
        return {"total_revenue": 0, "total_sales": 0, "total_products": 0, "total_views": 0, "recent_sales": [], "sales_by_day": []}
    
    workspace_id = membership["workspace_id"]
    products = await db.products.find({"workspace_id": workspace_id}, {"_id": 0}).to_list(100)
    
    total_revenue = sum(p.get("revenue", 0) for p in products)
    total_sales = sum(p.get("downloads", 0) for p in products)
    total_views = sum(p.get("views", 0) for p in products)
    
    return {
        "total_revenue": total_revenue,
        "total_sales": total_sales,
        "total_products": len(products),
        "total_views": total_views,
        "recent_sales": [],
        "sales_by_day": []
    }

# ==================== APP SETUP ====================

app.include_router(api_router)
app.include_router(admin_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
