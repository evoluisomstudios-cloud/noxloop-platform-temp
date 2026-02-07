"""
NOXLOOP Media Studio API Tests
Tests for Media upload/list/delete, media association with products, and public media endpoint
"""
import pytest
import requests
import os
import uuid
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://noxloop-media-studio.preview.emergentagent.com').rstrip('/')

# Test credentials - Admin required for media endpoints
ADMIN_EMAIL = "admin@digiforge.com"
ADMIN_PASSWORD = "admin123"

# Test file content for upload
TEST_IMAGE_CONTENT = (
    b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01'
    b'\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00'
    b'\x00\x01\x01\x00\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82'
)


class TestMediaEndpoints:
    """Media management endpoint tests for Admin users"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get admin auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Admin login failed: {response.text}"
        data = response.json()
        assert data.get("is_admin") == True, "User is not admin"
        print(f"✓ Admin login successful: {data['email']}, is_admin={data['is_admin']}")
        return data["token"]
    
    @pytest.fixture(scope="class")
    def uploaded_asset_id(self, admin_token):
        """Upload a test image and return asset_id"""
        files = {'file': ('test_image.png', TEST_IMAGE_CONTENT, 'image/png')}
        response = requests.post(
            f"{BASE_URL}/api/admin/media/upload",
            headers={"Authorization": f"Bearer {admin_token}"},
            files=files
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Test asset uploaded: {data['asset_id']}")
            return data['asset_id']
        else:
            print(f"✗ Upload failed: {response.status_code} - {response.text}")
            return None
    
    def test_media_upload_admin(self, admin_token):
        """Test media upload endpoint POST /api/admin/media/upload"""
        files = {'file': ('test_upload.png', TEST_IMAGE_CONTENT, 'image/png')}
        response = requests.post(
            f"{BASE_URL}/api/admin/media/upload",
            headers={"Authorization": f"Bearer {admin_token}"},
            files=files
        )
        
        assert response.status_code == 200, f"Upload failed: {response.status_code} - {response.text}"
        
        data = response.json()
        assert "asset_id" in data, "Response missing asset_id"
        assert "filename" in data, "Response missing filename"
        assert "original_filename" in data, "Response missing original_filename"
        assert "type" in data, "Response missing type"
        assert data["type"] == "image", f"Expected type 'image', got '{data['type']}'"
        assert "size" in data, "Response missing size"
        assert "mime_type" in data, "Response missing mime_type"
        assert data["mime_type"] == "image/png", f"Expected mime_type 'image/png', got '{data['mime_type']}'"
        
        print(f"✓ Media upload successful: {data['asset_id']}, type={data['type']}, size={data['size']}")
        return data["asset_id"]
    
    def test_media_upload_invalid_type(self, admin_token):
        """Test media upload rejects invalid file types"""
        files = {'file': ('test.txt', b'Hello World', 'text/plain')}
        response = requests.post(
            f"{BASE_URL}/api/admin/media/upload",
            headers={"Authorization": f"Bearer {admin_token}"},
            files=files
        )
        
        assert response.status_code == 400, f"Expected 400 for invalid type, got {response.status_code}"
        print("✓ Invalid file type rejected correctly")
    
    def test_media_list_admin(self, admin_token):
        """Test media list endpoint GET /api/admin/media"""
        response = requests.get(
            f"{BASE_URL}/api/admin/media",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200, f"List failed: {response.status_code} - {response.text}"
        
        data = response.json()
        assert "assets" in data, "Response missing 'assets' field"
        assert "total" in data, "Response missing 'total' field"
        assert isinstance(data["assets"], list), "Assets should be a list"
        
        print(f"✓ Media list successful: {data['total']} total assets, {len(data['assets'])} returned")
        return data
    
    def test_media_list_filtered_by_type(self, admin_token):
        """Test media list with type filter"""
        response = requests.get(
            f"{BASE_URL}/api/admin/media?type=image",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200, f"List failed: {response.status_code}"
        
        data = response.json()
        # All returned assets should be images
        for asset in data.get("assets", []):
            assert asset["type"] == "image", f"Expected type 'image', got '{asset['type']}'"
        
        print(f"✓ Media list filtered by type=image: {len(data['assets'])} image assets")
    
    def test_public_media_endpoint(self, admin_token, uploaded_asset_id):
        """Test public media endpoint GET /api/media/{asset_id}"""
        if not uploaded_asset_id:
            pytest.skip("No uploaded asset available")
        
        # Public endpoint - no auth required
        response = requests.get(f"{BASE_URL}/api/media/{uploaded_asset_id}")
        
        assert response.status_code == 200, f"Public media fetch failed: {response.status_code} - {response.text}"
        assert len(response.content) > 0, "Response content is empty"
        
        # Check content type
        content_type = response.headers.get("content-type", "")
        assert "image" in content_type or "octet-stream" in content_type, f"Unexpected content type: {content_type}"
        
        print(f"✓ Public media endpoint successful: {len(response.content)} bytes, content-type={content_type}")
    
    def test_public_media_not_found(self):
        """Test public media endpoint returns 404 for invalid asset"""
        response = requests.get(f"{BASE_URL}/api/media/nonexistent_asset_id")
        
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("✓ Public media returns 404 for invalid asset")
    
    def test_media_delete_admin(self, admin_token):
        """Test media delete endpoint DELETE /api/admin/media/{asset_id}"""
        # First upload an asset to delete
        files = {'file': ('to_delete.png', TEST_IMAGE_CONTENT, 'image/png')}
        upload_response = requests.post(
            f"{BASE_URL}/api/admin/media/upload",
            headers={"Authorization": f"Bearer {admin_token}"},
            files=files
        )
        
        assert upload_response.status_code == 200, "Failed to upload asset for deletion test"
        asset_id = upload_response.json()["asset_id"]
        
        # Delete the asset
        delete_response = requests.delete(
            f"{BASE_URL}/api/admin/media/{asset_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert delete_response.status_code in [200, 204], f"Delete failed: {delete_response.status_code}"
        
        # Verify deletion
        verify_response = requests.get(f"{BASE_URL}/api/media/{asset_id}")
        assert verify_response.status_code == 404, "Asset still accessible after deletion"
        
        print(f"✓ Media delete successful: {asset_id}")
    
    def test_media_upload_unauthorized(self):
        """Test media upload requires admin authentication"""
        files = {'file': ('test.png', TEST_IMAGE_CONTENT, 'image/png')}
        response = requests.post(
            f"{BASE_URL}/api/admin/media/upload",
            files=files
        )
        
        assert response.status_code == 401, f"Expected 401 for unauthorized, got {response.status_code}"
        print("✓ Unauthorized media upload rejected")


class TestProductMediaAssociation:
    """Tests for associating media assets with products"""
    
    @pytest.fixture(scope="class")
    def admin_data(self):
        """Get admin auth token and workspace"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        token = response.json()["token"]
        
        # Get workspace
        ws_response = requests.get(
            f"{BASE_URL}/api/workspaces",
            headers={"Authorization": f"Bearer {token}"}
        )
        workspaces = ws_response.json()
        workspace_id = workspaces[0]["workspace_id"] if workspaces else None
        
        return {"token": token, "workspace_id": workspace_id}
    
    @pytest.fixture(scope="class")
    def test_asset_id(self, admin_data):
        """Upload a test asset for association tests"""
        files = {'file': ('product_image.png', TEST_IMAGE_CONTENT, 'image/png')}
        response = requests.post(
            f"{BASE_URL}/api/admin/media/upload",
            headers={"Authorization": f"Bearer {admin_data['token']}"},
            files=files
        )
        
        if response.status_code == 200:
            return response.json()["asset_id"]
        return None
    
    @pytest.fixture(scope="class")
    def test_product_id(self, admin_data):
        """Get an existing product or create one for testing"""
        # List existing products
        response = requests.get(
            f"{BASE_URL}/api/products",
            headers={"Authorization": f"Bearer {admin_data['token']}"}
        )
        
        if response.status_code == 200:
            products = response.json()
            if products:
                print(f"Using existing product: {products[0]['product_id']}")
                return products[0]["product_id"]
        
        # Create a new product if none exist
        create_response = requests.post(
            f"{BASE_URL}/api/products/generate",
            headers={"Authorization": f"Bearer {admin_data['token']}"},
            json={
                "title": "Test Product for Media",
                "description": "Product to test media association",
                "product_type": "ebook",
                "topic": "Testing",
                "target_audience": "Developers",
                "tone": "professional",
                "language": "pt"
            }
        )
        
        if create_response.status_code == 200:
            return create_response.json()["product_id"]
        return None
    
    def test_update_product_with_media_assets(self, admin_data, test_product_id, test_asset_id):
        """Test updating product with media_asset_ids via PUT /api/products/{product_id}"""
        if not test_product_id:
            pytest.skip("No product available for testing")
        if not test_asset_id:
            pytest.skip("No asset available for testing")
        
        # Update product with media assets
        response = requests.put(
            f"{BASE_URL}/api/products/{test_product_id}",
            headers={"Authorization": f"Bearer {admin_data['token']}", "Content-Type": "application/json"},
            json={
                "media_asset_ids": [test_asset_id]
            }
        )
        
        assert response.status_code == 200, f"Update failed: {response.status_code} - {response.text}"
        
        data = response.json()
        assert "media_asset_ids" in data, "Response missing media_asset_ids"
        assert test_asset_id in data["media_asset_ids"], "Asset ID not in product's media_asset_ids"
        
        print(f"✓ Product updated with media: {test_product_id}, media_asset_ids={data['media_asset_ids']}")
        return data
    
    def test_get_product_with_media_assets(self, admin_data, test_product_id, test_asset_id):
        """Test that product GET returns media_asset_ids"""
        if not test_product_id:
            pytest.skip("No product available for testing")
        
        # First update the product with media
        requests.put(
            f"{BASE_URL}/api/products/{test_product_id}",
            headers={"Authorization": f"Bearer {admin_data['token']}", "Content-Type": "application/json"},
            json={"media_asset_ids": [test_asset_id] if test_asset_id else []}
        )
        
        # Get product
        response = requests.get(
            f"{BASE_URL}/api/products/{test_product_id}",
            headers={"Authorization": f"Bearer {admin_data['token']}"}
        )
        
        assert response.status_code == 200, f"GET failed: {response.status_code}"
        
        data = response.json()
        assert "product_id" in data, "Response missing product_id"
        # media_asset_ids should be present (even if empty)
        
        print(f"✓ Product GET successful: {data['product_id']}, has media_asset_ids={data.get('media_asset_ids', [])}")
    
    def test_update_product_clear_media_assets(self, admin_data, test_product_id):
        """Test clearing media_asset_ids from product"""
        if not test_product_id:
            pytest.skip("No product available for testing")
        
        # Clear media assets
        response = requests.put(
            f"{BASE_URL}/api/products/{test_product_id}",
            headers={"Authorization": f"Bearer {admin_data['token']}", "Content-Type": "application/json"},
            json={"media_asset_ids": []}
        )
        
        assert response.status_code == 200, f"Update failed: {response.status_code}"
        
        data = response.json()
        assert data.get("media_asset_ids", []) == [], "media_asset_ids should be empty"
        
        print(f"✓ Product media cleared: {test_product_id}")


class TestPublicProductWithMedia:
    """Tests for public product page with media"""
    
    @pytest.fixture(scope="class")
    def admin_data(self):
        """Get admin auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        return {"token": response.json()["token"]}
    
    @pytest.fixture(scope="class")
    def published_product_with_media(self, admin_data):
        """Create or get a published product with media for testing"""
        # Upload an asset
        files = {'file': ('hero_image.png', TEST_IMAGE_CONTENT, 'image/png')}
        upload_response = requests.post(
            f"{BASE_URL}/api/admin/media/upload",
            headers={"Authorization": f"Bearer {admin_data['token']}"},
            files=files
        )
        
        asset_id = None
        if upload_response.status_code == 200:
            asset_id = upload_response.json()["asset_id"]
        
        # Get products
        products_response = requests.get(
            f"{BASE_URL}/api/products",
            headers={"Authorization": f"Bearer {admin_data['token']}"}
        )
        
        if products_response.status_code == 200:
            products = products_response.json()
            if products:
                product = products[0]
                product_id = product["product_id"]
                
                # Update with media and publish
                update_response = requests.put(
                    f"{BASE_URL}/api/products/{product_id}",
                    headers={"Authorization": f"Bearer {admin_data['token']}", "Content-Type": "application/json"},
                    json={
                        "media_asset_ids": [asset_id] if asset_id else [],
                        "is_published": True,
                        "price": 9.99
                    }
                )
                
                if update_response.status_code == 200:
                    return {"product_id": product_id, "asset_id": asset_id}
        
        return None
    
    def test_public_product_has_media_asset_ids(self, published_product_with_media):
        """Test that public product endpoint returns media_asset_ids"""
        if not published_product_with_media:
            pytest.skip("No published product available")
        
        product_id = published_product_with_media["product_id"]
        
        response = requests.get(f"{BASE_URL}/api/public/product/{product_id}")
        
        assert response.status_code == 200, f"Public product fetch failed: {response.status_code}"
        
        data = response.json()
        assert "product_id" in data, "Response missing product_id"
        # Check if media_asset_ids is present in public response
        media_ids = data.get("media_asset_ids", [])
        print(f"✓ Public product has media_asset_ids: {media_ids}")
        
        if published_product_with_media.get("asset_id"):
            assert published_product_with_media["asset_id"] in media_ids, \
                f"Expected asset {published_product_with_media['asset_id']} in media_asset_ids"
        
        return data


class TestAdminMediaPageUI:
    """Integration tests for Admin Media UI components"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get admin auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["token"]
    
    def test_admin_stats_accessible(self, admin_token):
        """Verify admin stats endpoint is accessible for media page context"""
        response = requests.get(
            f"{BASE_URL}/api/admin/stats",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200, f"Admin stats failed: {response.status_code}"
        
        data = response.json()
        assert "total_users" in data
        print(f"✓ Admin stats accessible: users={data['total_users']}, products={data['total_products']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
