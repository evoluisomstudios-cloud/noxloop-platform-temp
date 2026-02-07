"""
Pydantic Models for DigiForge
"""
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import datetime

# ==================== ENUMS ====================

class UserRole(str, Enum):
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"

class PlanType(str, Enum):
    FREE = "free"
    STARTER = "starter"
    PRO = "pro"
    ENTERPRISE = "enterprise"

class FeatureFlag(str, Enum):
    UNLIMITED_EXPORTS = "unlimited_exports"
    PRIORITY_GENERATION = "priority_generation"
    CUSTOM_TEMPLATES = "custom_templates"
    API_ACCESS = "api_access"
    WHITE_LABEL = "white_label"
    RAG_ACCESS = "rag_access"

# ==================== USER MODELS ====================

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    user_id: str
    email: str
    name: str
    picture: Optional[str] = None
    is_admin: bool = False
    created_at: Optional[str] = None

class UserWithWorkspaces(UserResponse):
    workspaces: List[Dict[str, Any]] = []

# ==================== WORKSPACE MODELS ====================

class WorkspaceCreate(BaseModel):
    name: str
    description: Optional[str] = None

class WorkspaceUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

class WorkspaceResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    workspace_id: str
    name: str
    description: Optional[str] = None
    owner_id: str
    plan: PlanType = PlanType.FREE
    credits: int = 10
    features: List[str] = []
    created_at: str
    updated_at: str

class WorkspaceMember(BaseModel):
    user_id: str
    email: str
    name: str
    role: UserRole
    joined_at: str

class WorkspaceInvite(BaseModel):
    email: EmailStr
    role: UserRole = UserRole.MEMBER

# ==================== PRODUCT MODELS ====================

class ProductCreate(BaseModel):
    title: str
    description: str
    product_type: str  # ebook, guide, course, template
    topic: str
    target_audience: str
    tone: str = "professional"
    language: str = "pt"

class ProductUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    is_published: Optional[bool] = None
    landing_page: Optional[Dict[str, Any]] = None

class ProductResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    product_id: str
    workspace_id: str
    user_id: str
    title: str
    description: str
    product_type: str
    content: Optional[str] = None
    price: float = 0.0
    is_published: bool = False
    landing_page: Optional[Dict[str, Any]] = None
    downloads: int = 0
    revenue: float = 0.0
    views: int = 0
    created_at: str
    updated_at: str

# ==================== CAMPAIGN MODELS ====================

class CampaignCreate(BaseModel):
    niche: str
    product: str
    offer: str
    price: str
    objective: str  # leads / vendas
    tone: str
    channel: str  # IG / FB / Google / email
    language: str = "pt"
    use_rag: bool = True

class CampaignResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    campaign_id: str
    workspace_id: str
    user_id: str
    config: Dict[str, Any]
    assets: Dict[str, Any]
    rag_used: bool
    created_at: str

# ==================== TEMPLATE MODELS (Admin) ====================

class TemplateCreate(BaseModel):
    name: str
    description: str
    category: str  # product, campaign, email, landing
    prompt_template: str
    variables: List[str] = []
    is_active: bool = True

class TemplateUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    prompt_template: Optional[str] = None
    variables: Optional[List[str]] = None
    is_active: Optional[bool] = None

class TemplateResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    template_id: str
    name: str
    description: str
    category: str
    prompt_template: str
    variables: List[str]
    is_active: bool
    usage_count: int = 0
    created_at: str
    updated_at: str

# ==================== PLAN MODELS (Admin) ====================

class PlanConfig(BaseModel):
    plan_id: PlanType
    name: str
    price: float
    credits_monthly: int
    features: List[FeatureFlag]
    max_workspaces: int = 1
    max_members_per_workspace: int = 1
    is_active: bool = True

class PlanUpdate(BaseModel):
    name: Optional[str] = None
    price: Optional[float] = None
    credits_monthly: Optional[int] = None
    features: Optional[List[FeatureFlag]] = None
    max_workspaces: Optional[int] = None
    max_members_per_workspace: Optional[int] = None
    is_active: Optional[bool] = None

# ==================== USAGE MODELS ====================

class UsageRecord(BaseModel):
    workspace_id: str
    user_id: str
    action: str  # generation, export, api_call
    credits_used: int = 1
    metadata: Dict[str, Any] = {}

class UsageStats(BaseModel):
    workspace_id: str
    period: str  # daily, monthly
    total_generations: int = 0
    total_exports: int = 0
    total_api_calls: int = 0
    credits_used: int = 0
    estimated_cost: float = 0.0

# ==================== ADMIN MODELS ====================

class AdminStats(BaseModel):
    total_users: int
    total_workspaces: int
    total_products: int
    total_campaigns: int
    total_generations: int
    total_exports: int
    active_subscriptions: int
    revenue_total: float
    usage_today: int
    usage_month: int
    llm_provider: str
    rag_enabled: bool
    stripe_enabled: bool

class AdminUserList(BaseModel):
    users: List[UserResponse]
    total: int
    page: int
    per_page: int

# ==================== PAYMENT MODELS ====================

class CheckoutRequest(BaseModel):
    product_id: str
    origin_url: str
    customer_email: Optional[str] = None

class SubscriptionRequest(BaseModel):
    plan_id: PlanType
    origin_url: str

class GoogleAuthRequest(BaseModel):
    code: str
    redirect_uri: str

# ==================== SYSTEM STATUS ====================

class SystemStatus(BaseModel):
    version: str
    llm_provider: str
    llm_available: bool
    rag_enabled: bool
    rag_available: bool
    stripe_enabled: bool
    webhooks_enabled: bool
    database_connected: bool
