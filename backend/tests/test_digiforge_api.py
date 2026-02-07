"""
DigiForge API Tests
Tests for authentication, workspaces, products, campaigns, and admin endpoints
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://noxloop-media-studio.preview.emergentagent.com').rstrip('/')

# Test credentials
ADMIN_EMAIL = "admin@digiforge.com"
ADMIN_PASSWORD = "admin123"
TEST_USER_EMAIL = f"test_{uuid.uuid4().hex[:8]}@test.com"
TEST_USER_PASSWORD = "testpass123"
TEST_USER_NAME = "Test User"


class TestSystemStatus:
    """System status endpoint tests"""
    
    def test_status_endpoint(self):
        """Test /api/status returns correct system info"""
        response = requests.get(f"{BASE_URL}/api/status")
        assert response.status_code == 200
        
        data = response.json()
        assert "llm_provider" in data
        assert data["llm_provider"] == "mock"
        assert "database_connected" in data
        assert data["database_connected"] == True
        assert "version" in data
        print(f"✓ Status: LLM={data['llm_provider']}, DB={data['database_connected']}")


class TestAuthEndpoints:
    """Authentication endpoint tests"""
    
    @pytest.fixture(scope="class")
    def session(self):
        return requests.Session()
    
    def test_register_new_user(self, session):
        """Test user registration"""
        response = session.post(f"{BASE_URL}/api/auth/register", json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD,
            "name": TEST_USER_NAME
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "user_id" in data
        assert data["email"] == TEST_USER_EMAIL
        assert "token" in data
        assert "default_workspace_id" in data
        print(f"✓ Registered user: {data['email']}")
    
    def test_register_duplicate_email(self, session):
        """Test duplicate email registration fails"""
        response = session.post(f"{BASE_URL}/api/auth/register", json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD,
            "name": TEST_USER_NAME
        })
        
        assert response.status_code == 400
        data = response.json()
        assert "already registered" in data.get("detail", "").lower()
        print("✓ Duplicate email rejected correctly")
    
    def test_login_valid_credentials(self, session):
        """Test login with valid credentials"""
        response = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "user_id" in data
        assert "token" in data
        assert data["email"] == TEST_USER_EMAIL
        print(f"✓ Login successful: {data['email']}")
    
    def test_login_invalid_credentials(self, session):
        """Test login with invalid credentials"""
        response = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "wrong@email.com",
            "password": "wrongpassword"
        })
        
        assert response.status_code == 401
        print("✓ Invalid credentials rejected correctly")
    
    def test_get_me_authenticated(self, session):
        """Test /api/auth/me with valid token"""
        # First login to get token
        login_response = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        })
        token = login_response.json().get("token")
        
        # Get user profile
        response = session.get(
            f"{BASE_URL}/api/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == TEST_USER_EMAIL
        assert "workspaces" in data
        print(f"✓ Profile retrieved: {data['email']}, workspaces: {len(data['workspaces'])}")
    
    def test_get_me_unauthenticated(self, session):
        """Test /api/auth/me without token"""
        response = requests.get(f"{BASE_URL}/api/auth/me")
        assert response.status_code == 401
        print("✓ Unauthenticated access rejected correctly")


class TestAdminLogin:
    """Admin user login tests"""
    
    def test_admin_login(self):
        """Test admin user login"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == ADMIN_EMAIL
        assert data.get("is_admin") == True
        print(f"✓ Admin login successful: {data['email']}, is_admin={data['is_admin']}")
        return data["token"]


class TestWorkspaceEndpoints:
    """Workspace endpoint tests"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get auth token for test user"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        # If test user doesn't exist, register
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD,
            "name": TEST_USER_NAME
        })
        return response.json().get("token")
    
    def test_list_workspaces(self, auth_token):
        """Test listing user workspaces"""
        response = requests.get(
            f"{BASE_URL}/api/workspaces",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1  # At least default workspace
        print(f"✓ Workspaces listed: {len(data)} workspace(s)")
        return data[0]["workspace_id"] if data else None
    
    def test_list_workspaces_unauthenticated(self):
        """Test listing workspaces without auth"""
        response = requests.get(f"{BASE_URL}/api/workspaces")
        assert response.status_code == 401
        print("✓ Unauthenticated workspace access rejected")


class TestProductEndpoints:
    """Product endpoint tests"""
    
    @pytest.fixture(scope="class")
    def auth_data(self):
        """Get auth token and workspace ID"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        token = response.json().get("token")
        
        # Get workspace
        ws_response = requests.get(
            f"{BASE_URL}/api/workspaces",
            headers={"Authorization": f"Bearer {token}"}
        )
        workspaces = ws_response.json()
        workspace_id = workspaces[0]["workspace_id"] if workspaces else None
        
        return {"token": token, "workspace_id": workspace_id}
    
    def test_generate_product_legacy(self, auth_data):
        """Test legacy product generation endpoint (uses mock LLM)"""
        response = requests.post(
            f"{BASE_URL}/api/products/generate",
            headers={"Authorization": f"Bearer {auth_data['token']}"},
            json={
                "title": "Test eBook",
                "description": "A test digital product",
                "product_type": "ebook",
                "topic": "Digital Marketing",
                "target_audience": "Entrepreneurs",
                "tone": "professional",
                "language": "pt"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "product_id" in data
        assert "content" in data
        assert "Mock Generated Content" in data["content"]  # Mock provider response
        print(f"✓ Product generated (mock): {data['product_id']}")
    
    def test_list_products(self, auth_data):
        """Test listing products"""
        response = requests.get(
            f"{BASE_URL}/api/products",
            headers={"Authorization": f"Bearer {auth_data['token']}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Products listed: {len(data)} product(s)")


class TestCampaignEndpoints:
    """Campaign endpoint tests"""
    
    @pytest.fixture(scope="class")
    def auth_data(self):
        """Get auth token and workspace ID"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        token = response.json().get("token")
        
        # Get workspace
        ws_response = requests.get(
            f"{BASE_URL}/api/workspaces",
            headers={"Authorization": f"Bearer {token}"}
        )
        workspaces = ws_response.json()
        workspace_id = workspaces[0]["workspace_id"] if workspaces else None
        
        return {"token": token, "workspace_id": workspace_id}
    
    def test_generate_campaign(self, auth_data):
        """Test campaign generation endpoint (uses mock LLM)"""
        response = requests.post(
            f"{BASE_URL}/api/workspaces/{auth_data['workspace_id']}/campaigns/generate",
            headers={"Authorization": f"Bearer {auth_data['token']}"},
            json={
                "niche": "Fitness",
                "product": "Online Training Program",
                "offer": "50% discount",
                "price": "€97",
                "objective": "vendas",
                "tone": "professional",
                "channel": "instagram",
                "language": "pt",
                "use_rag": False
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "campaign_id" in data
        assert "assets" in data
        assert "landing_copy" in data["assets"]
        assert "ad_variations" in data["assets"]
        print(f"✓ Campaign generated (mock): {data['campaign_id']}")
        return data["campaign_id"]
    
    def test_list_campaigns(self, auth_data):
        """Test listing campaigns"""
        response = requests.get(
            f"{BASE_URL}/api/workspaces/{auth_data['workspace_id']}/campaigns",
            headers={"Authorization": f"Bearer {auth_data['token']}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Campaigns listed: {len(data)} campaign(s)")


class TestAdminEndpoints:
    """Admin endpoint tests"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get admin auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        return response.json().get("token")
    
    @pytest.fixture(scope="class")
    def regular_token(self):
        """Get regular user auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        return None
    
    def test_admin_stats(self, admin_token):
        """Test admin stats endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/admin/stats",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "total_users" in data
        assert "total_workspaces" in data
        assert "total_products" in data
        assert "total_campaigns" in data
        assert "llm_provider" in data
        assert data["llm_provider"] == "mock"
        print(f"✓ Admin stats: users={data['total_users']}, workspaces={data['total_workspaces']}, llm={data['llm_provider']}")
    
    def test_admin_stats_non_admin(self, regular_token):
        """Test admin stats endpoint with non-admin user"""
        if not regular_token:
            pytest.skip("Regular user token not available")
        
        response = requests.get(
            f"{BASE_URL}/api/admin/stats",
            headers={"Authorization": f"Bearer {regular_token}"}
        )
        
        assert response.status_code == 403
        print("✓ Non-admin access to admin stats rejected")
    
    def test_admin_users_list(self, admin_token):
        """Test admin users list endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/admin/users",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "users" in data
        assert "total" in data
        assert isinstance(data["users"], list)
        print(f"✓ Admin users list: {data['total']} total users")
    
    def test_admin_templates_list(self, admin_token):
        """Test admin templates list endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/admin/templates",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Admin templates list: {len(data)} templates")


class TestBillingEndpoints:
    """Billing endpoint tests"""
    
    def test_get_billing_plans(self):
        """Test billing plans endpoint"""
        response = requests.get(f"{BASE_URL}/api/billing/plans")
        
        assert response.status_code == 200
        data = response.json()
        assert "free" in data
        assert "starter" in data
        assert "pro" in data
        assert "enterprise" in data
        assert data["free"]["price"] == 0
        print(f"✓ Billing plans retrieved: {list(data.keys())}")


class TestAnalyticsEndpoints:
    """Analytics endpoint tests"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        return response.json().get("token")
    
    def test_get_analytics(self, auth_token):
        """Test analytics endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/analytics",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "total_revenue" in data
        assert "total_sales" in data
        assert "total_products" in data
        print(f"✓ Analytics: products={data['total_products']}, revenue={data['total_revenue']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
