# API Documentation with drf-spectacular

This Django project uses `drf-spectacular` to automatically generate OpenAPI 3.0 schema and provide interactive API documentation.

## Installation and Configuration

`drf-spectacular` has been installed and configured in the project with the following features:

### Available Endpoints

Once the development server is running, you can access:

1. **OpenAPI Schema** (JSON/YAML): `http://localhost:8000/api/schema/`
   - Raw OpenAPI 3.0 schema specification
   - Can be used with external tools like Postman, Insomnia, etc.

2. **Swagger UI**: `http://localhost:8000/api/docs/`
   - Interactive API documentation
   - Test API endpoints directly from the browser
   - Requires authentication for protected endpoints

3. **ReDoc**: `http://localhost:8000/api/redoc/`
   - Alternative documentation interface
   - Clean, responsive design
   - Better for API reference documentation

### Configuration Details

The following settings have been configured in `settings.py`:

```python
# In INSTALLED_APPS
'drf_spectacular',

# REST Framework configuration
REST_FRAMEWORK = {
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    # ... other settings
}

# drf-spectacular specific settings
SPECTACULAR_SETTINGS = {
    'TITLE': 'Stand-up App API',
    'DESCRIPTION': 'API for managing team stand-ups and Slack integration',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'COMPONENT_SPLIT_REQUEST': True,
    'SCHEMA_PATH_PREFIX': '/api/',
    'SERVE_PERMISSIONS': ['rest_framework.permissions.IsAuthenticated'],
    'SERVE_AUTHENTICATION': ['rest_framework.authentication.SessionAuthentication'],
}
```

### Usage Examples

#### Generate Schema File

```bash
# Generate OpenAPI schema file
pipenv run python manage.py spectacular --color --file schema.yml

# Generate JSON schema
pipenv run python manage.py spectacular --format openapi-json --file schema.json
```

#### Enhanced View Documentation

Views can be enhanced with drf-spectacular decorators for better documentation:

```python
from drf_spectacular.utils import extend_schema, extend_schema_view

@extend_schema_view(
    list=extend_schema(
        description="List all standups",
        summary="List standups",
        tags=["Standups"]
    ),
)
class StandupViewSet(viewsets.ModelViewSet):
    # ... view implementation
```

### Authentication

The API documentation endpoints require authentication. Make sure to:

1. Create a user account through Django admin or authentication endpoints
2. Log in to access the documentation
3. Use the "Authorize" button in Swagger UI to authenticate

### Testing

Run the included test to verify API documentation is working:

```bash
pipenv run python manage.py test test_api_docs
```

### Development Tips

1. **Auto-generated Documentation**: Schema is automatically generated from your serializers and views
2. **Custom Descriptions**: Use `@extend_schema` decorators for custom endpoint descriptions
3. **Tags**: Organize endpoints using tags for better navigation
4. **Response Examples**: Serializers automatically provide response examples
5. **Request Examples**: Use serializers to show request body examples

### Security Considerations

- Documentation endpoints are protected by authentication
- Schema generation respects DRF permissions
- No sensitive data is exposed in the generated schema
- Production deployments should consider additional access controls
