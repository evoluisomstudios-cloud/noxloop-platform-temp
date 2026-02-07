import requests
import sys
import json
from datetime import datetime

class SaaSAPITester:
    def __init__(self, base_url="https://noxloop-media-studio.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.token = None
        self.user_data = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

    def log_test(self, name, success, details=""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name} - PASSED")
        else:
            print(f"❌ {name} - FAILED: {details}")
        
        self.test_results.append({
            "test": name,
            "success": success,
            "details": details
        })

    def test_billing_plans(self):
        """Test billing plans endpoint"""
        try:
            response = requests.get(f"{self.base_url}/billing/plans")
            success = response.status_code == 200
            details = f"Status: {response.status_code}"
            if success:
                plans = response.json()
                details += f", Plans: {list(plans.keys())}"
            self.log_test("GET /billing/plans", success, details)
            return success
        except Exception as e:
            self.log_test("GET /billing/plans", False, str(e))
            return False

    def test_register(self, email, password, name):
        """Test user registration"""
        try:
            data = {"email": email, "password": password, "name": name}
            response = requests.post(
                f"{self.base_url}/auth/register",
                json=data,
                headers={"Content-Type": "application/json"}
            )
            
            success = response.status_code == 200
            details = f"Status: {response.status_code}"
            
            if success:
                self.user_data = response.json()
                self.token = self.user_data.get("token")
                details += f", User ID: {self.user_data.get('user_id')}"
            else:
                try:
                    error_data = response.json()
                    details += f", Error: {error_data.get('detail', 'Unknown error')}"
                except:
                    details += f", Response: {response.text[:100]}"
            
            self.log_test("POST /auth/register", success, details)
            return success
        except Exception as e:
            self.log_test("POST /auth/register", False, str(e))
            return False

    def test_login(self, email, password):
        """Test user login"""
        try:
            data = {"email": email, "password": password}
            response = requests.post(
                f"{self.base_url}/auth/login",
                json=data,
                headers={"Content-Type": "application/json"}
            )
            
            success = response.status_code == 200
            details = f"Status: {response.status_code}"
            
            if success:
                self.user_data = response.json()
                self.token = self.user_data.get("token")
                details += f", User ID: {self.user_data.get('user_id')}"
            else:
                try:
                    error_data = response.json()
                    details += f", Error: {error_data.get('detail', 'Unknown error')}"
                except:
                    details += f", Response: {response.text[:100]}"
            
            self.log_test("POST /auth/login", success, details)
            return success
        except Exception as e:
            self.log_test("POST /auth/login", False, str(e))
            return False

    def test_auth_me(self):
        """Test get current user"""
        if not self.token:
            self.log_test("GET /auth/me", False, "No token available")
            return False
        
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            response = requests.get(f"{self.base_url}/auth/me", headers=headers)
            
            success = response.status_code == 200
            details = f"Status: {response.status_code}"
            
            if success:
                user_data = response.json()
                details += f", Email: {user_data.get('email')}"
            
            self.log_test("GET /auth/me", success, details)
            return success
        except Exception as e:
            self.log_test("GET /auth/me", False, str(e))
            return False

    def test_get_products(self):
        """Test get user products"""
        if not self.token:
            self.log_test("GET /products", False, "No token available")
            return False
        
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            response = requests.get(f"{self.base_url}/products", headers=headers)
            
            success = response.status_code == 200
            details = f"Status: {response.status_code}"
            
            if success:
                products = response.json()
                details += f", Products count: {len(products)}"
            
            self.log_test("GET /products", success, details)
            return success
        except Exception as e:
            self.log_test("GET /products", False, str(e))
            return False

    def test_generate_product(self):
        """Test AI product generation"""
        if not self.token:
            self.log_test("POST /products/generate", False, "No token available")
            return False
        
        try:
            headers = {"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"}
            data = {
                "title": "Test eBook",
                "description": "A test ebook for API testing",
                "product_type": "ebook",
                "topic": "API Testing",
                "target_audience": "Developers",
                "tone": "professional",
                "language": "pt"
            }
            
            response = requests.post(
                f"{self.base_url}/products/generate",
                json=data,
                headers=headers
            )
            
            success = response.status_code == 200
            details = f"Status: {response.status_code}"
            
            if success:
                product = response.json()
                details += f", Product ID: {product.get('product_id')}"
                return product.get('product_id')
            else:
                try:
                    error_data = response.json()
                    details += f", Error: {error_data.get('detail', 'Unknown error')}"
                except:
                    details += f", Response: {response.text[:100]}"
            
            self.log_test("POST /products/generate", success, details)
            return success
        except Exception as e:
            self.log_test("POST /products/generate", False, str(e))
            return False

    def test_get_analytics(self):
        """Test analytics endpoint"""
        if not self.token:
            self.log_test("GET /analytics", False, "No token available")
            return False
        
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            response = requests.get(f"{self.base_url}/analytics", headers=headers)
            
            success = response.status_code == 200
            details = f"Status: {response.status_code}"
            
            if success:
                analytics = response.json()
                details += f", Revenue: €{analytics.get('total_revenue', 0)}, Products: {analytics.get('total_products', 0)}"
            
            self.log_test("GET /analytics", success, details)
            return success
        except Exception as e:
            self.log_test("GET /analytics", False, str(e))
            return False

    def test_logout(self):
        """Test user logout"""
        if not self.token:
            self.log_test("POST /auth/logout", False, "No token available")
            return False
        
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            response = requests.post(f"{self.base_url}/auth/logout", headers=headers)
            
            success = response.status_code == 200
            details = f"Status: {response.status_code}"
            
            self.log_test("POST /auth/logout", success, details)
            return success
        except Exception as e:
            self.log_test("POST /auth/logout", False, str(e))
            return False

def main():
    print("🚀 Starting SaaS Platform API Tests")
    print("=" * 50)
    
    tester = SaaSAPITester()
    
    # Generate unique test user
    timestamp = datetime.now().strftime("%H%M%S")
    test_email = f"test_{timestamp}@example.com"
    test_password = "TestPass123!"
    test_name = f"Test User {timestamp}"
    
    print(f"📧 Test user: {test_email}")
    print()
    
    # Test sequence
    tests_sequence = [
        ("Billing Plans", lambda: tester.test_billing_plans()),
        ("User Registration", lambda: tester.test_register(test_email, test_password, test_name)),
        ("Auth Me", lambda: tester.test_auth_me()),
        ("Get Products", lambda: tester.test_get_products()),
        ("Get Analytics", lambda: tester.test_get_analytics()),
        ("Generate Product", lambda: tester.test_generate_product()),
        ("User Logout", lambda: tester.test_logout()),
        ("User Login", lambda: tester.test_login(test_email, test_password)),
    ]
    
    for test_name, test_func in tests_sequence:
        print(f"🔍 Testing {test_name}...")
        try:
            test_func()
        except Exception as e:
            tester.log_test(test_name, False, f"Exception: {str(e)}")
        print()
    
    # Summary
    print("=" * 50)
    print(f"📊 Test Results: {tester.tests_passed}/{tester.tests_run} passed")
    
    if tester.tests_passed == tester.tests_run:
        print("🎉 All tests passed!")
        return 0
    else:
        print("⚠️  Some tests failed. Check details above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())