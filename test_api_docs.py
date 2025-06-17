"""
Test file to demonstrate drf-spectacular integration
Run this after starting the development server to check API documentation
"""

from django.urls import reverse
from rest_framework.test import APITestCase
from django.contrib.auth.models import User


class APIDocumentationTestCase(APITestCase):
    """Test case to verify API documentation endpoints are working"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_schema_endpoint_accessible(self):
        """Test that the OpenAPI schema endpoint is accessible"""
        # Login user first
        self.client.force_authenticate(user=self.user)
        
        # Test schema endpoint
        url = reverse('schema')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['content-type'], 'application/vnd.oai.openapi')

    def test_swagger_ui_accessible(self):
        """Test that Swagger UI is accessible"""
        # Login user first  
        self.client.force_authenticate(user=self.user)
        
        # Test Swagger UI endpoint
        url = reverse('swagger-ui')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'swagger-ui')

    def test_redoc_accessible(self):
        """Test that ReDoc UI is accessible"""
        # Login user first
        self.client.force_authenticate(user=self.user)
        
        # Test ReDoc endpoint
        url = reverse('redoc')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'redoc')
