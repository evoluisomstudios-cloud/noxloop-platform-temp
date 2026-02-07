from fastapi import FastAPI, APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr, ConfigDict
from typing import List, Optional
import uuid
from datetime import datetime, timezone, timedelta
import jwt
from passlib.context import CryptContext

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Security
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
JWT_SECRET = os.environ.get('JWT_SECRET_KEY', 'your-secret-key-change-in-production')
JWT_ALGORITHM = "HS256"
security = HTTPBearer()

# Create the main app
app = FastAPI(title="NOXLOOP API")
api_router = APIRouter(prefix="/api")

# Models
class User(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: EmailStr
    name: str
    password_hash: str
    credits: int = 0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class UserCreate(BaseModel):
    email: EmailStr
    name: str
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    credits: int

class Product(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    deliverables: List[str]
    price: float
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ProductCreate(BaseModel):
    name: str
    description: str
    deliverables: List[str]
    price: float

class AIGenerationRequest(BaseModel):
    prompt: str
    template: Optional[str] = None

class AIGenerationResponse(BaseModel):
    id: str
    content: str
    credits_used: int
    created_at: datetime

# Helper functions
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=30)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    try:
        token = credentials.credentials
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Token inválido")
        
        user = await db.users.find_one({"id": user_id}, {"_id": 0})
        if user is None:
            raise HTTPException(status_code=401, detail="Utilizador não encontrado")
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirado")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Token inválido")

# Auth endpoints
@api_router.post("/auth/register")
async def register(user_data: UserCreate):
    # Check if user exists
    existing = await db.users.find_one({"email": user_data.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email já registado")
    
    # Create user
    user = User(
        email=user_data.email,
        name=user_data.name,
        password_hash=hash_password(user_data.password),
        credits=10  # Give 10 free credits on signup
    )
    
    doc = user.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    await db.users.insert_one(doc)
    
    # Create token
    token = create_access_token({"sub": user.id})
    
    return {
        "user": UserResponse(
            id=user.id,
            email=user.email,
            name=user.name,
            credits=user.credits
        ),
        "token": token
    }

@api_router.post("/auth/login")
async def login(credentials: UserLogin):
    user = await db.users.find_one({"email": credentials.email}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=401, detail="Email ou password incorretos")
    
    if not verify_password(credentials.password, user['password_hash']):
        raise HTTPException(status_code=401, detail="Email ou password incorretos")
    
    token = create_access_token({"sub": user['id']})
    
    return {
        "user": UserResponse(
            id=user['id'],
            email=user['email'],
            name=user['name'],
            credits=user['credits']
        ),
        "token": token
    }

@api_router.get("/auth/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    return UserResponse(
        id=current_user['id'],
        email=current_user['email'],
        name=current_user['name'],
        credits=current_user['credits']
    )

# Products endpoints
@api_router.get("/products", response_model=List[Product])
async def get_products():
    products = await db.products.find({}, {"_id": 0}).to_list(100)
    for product in products:
        if isinstance(product['created_at'], str):
            product['created_at'] = datetime.fromisoformat(product['created_at'])
    return products

@api_router.post("/products", response_model=Product)
async def create_product(product_data: ProductCreate, current_user: dict = Depends(get_current_user)):
    product = Product(**product_data.model_dump())
    doc = product.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    await db.products.insert_one(doc)
    return product

@api_router.get("/products/{product_id}", response_model=Product)
async def get_product(product_id: str):
    product = await db.products.find_one({"id": product_id}, {"_id": 0})
    if not product:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    if isinstance(product['created_at'], str):
        product['created_at'] = datetime.fromisoformat(product['created_at'])
    return product

# AI Generation endpoint
@api_router.post("/ai/generate", response_model=AIGenerationResponse)
async def generate_with_ai(request: AIGenerationRequest, current_user: dict = Depends(get_current_user)):
    CREDIT_COST = 5
    
    # Check credits
    if current_user['credits'] < CREDIT_COST:
        raise HTTPException(
            status_code=402,
            detail=f"Créditos insuficientes. Necessário: {CREDIT_COST}, Disponível: {current_user['credits']}"
        )
    
    # Deduct credits
    await db.users.update_one(
        {"id": current_user['id']},
        {"$inc": {"credits": -CREDIT_COST}}
    )
    
    # Generate content (mock for now)
    content = f"Conteúdo gerado com IA para: {request.prompt}\n\nTemplate: {request.template or 'Personalizado'}\n\nEste é um conteúdo de exemplo. Integre com OpenAI API para produção."
    
    generation = AIGenerationResponse(
        id=str(uuid.uuid4()),
        content=content,
        credits_used=CREDIT_COST,
        created_at=datetime.now(timezone.utc)
    )
    
    # Save to database
    doc = generation.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    doc['user_id'] = current_user['id']
    await db.generations.insert_one(doc)
    
    return generation

@api_router.get("/ai/generations")
async def get_my_generations(current_user: dict = Depends(get_current_user)):
    generations = await db.generations.find(
        {"user_id": current_user['id']},
        {"_id": 0}
    ).sort("created_at", -1).to_list(50)
    
    for gen in generations:
        if isinstance(gen['created_at'], str):
            gen['created_at'] = datetime.fromisoformat(gen['created_at'])
    
    return generations

# Health check
@api_router.get("/")
async def root():
    return {"message": "NOXLOOP API", "status": "running"}

# Include router
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()

@app.on_event("startup")
async def startup_seed_products():
    """Seed initial products if database is empty"""
    count = await db.products.count_documents({})
    if count == 0:
        initial_products = [
            {
                "id": str(uuid.uuid4()),
                "name": "Página de Captação de Leads",
                "description": "Landing page profissional otimizada para captar leads. Inclui formulário integrado, design responsivo e copy persuasiva.",
                "deliverables": [
                    "Landing page responsiva",
                    "Formulário de captação",
                    "Copy persuasiva otimizada",
                    "Integração com email marketing"
                ],
                "price": 49.99,
                "created_at": datetime.now(timezone.utc).isoformat()
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Pack eBook + Página de Vendas",
                "description": "eBook profissional com 20-30 páginas + landing page de vendas otimizada para conversão.",
                "deliverables": [
                    "eBook formato PDF (20-30 páginas)",
                    "Capa profissional",
                    "Landing page de vendas",
                    "Copy de vendas otimizada"
                ],
                "price": 99.99,
                "created_at": datetime.now(timezone.utc).isoformat()
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Mini-Funil Automático",
                "description": "Funil completo com landing page + página de obrigado + sequência de 3 emails automatizados.",
                "deliverables": [
                    "Landing page de captação",
                    "Página de obrigado",
                    "3 emails de follow-up",
                    "Estratégia de conversão"
                ],
                "price": 149.99,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
        ]
        await db.products.insert_many(initial_products)
        logger.info("Seeded initial products")