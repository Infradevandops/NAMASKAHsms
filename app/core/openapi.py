"""OpenAPI/Swagger documentation configuration."""


from fastapi.openapi.utils import get_openapi

def get_openapi_schema(app: FastAPI) -> dict:

    """Generate OpenAPI schema for API documentation."""
if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title="Namaskah SMS Verification API",
        version="2.4.0",
        description="SMS Verification Platform with Multi - Provider Support",
        routes=app.routes,
    )

    # Add security schemes
    openapi_schema["components"]["securitySchemes"] = {
        "bearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "JWT Bearer token for authentication",
        },
        "apiKey": {
            "type": "apiKey",
            "in": "header",
            "name": "X - API-Key",
            "description": "API Key for service - to-service authentication",
        },
    }

    # Add tags
    openapi_schema["tags"] = [
        {"name": "Verification", "description": "SMS verification operations"},
        {"name": "Rentals", "description": "Phone number rental operations"},
        {"name": "Wallet", "description": "User wallet and balance operations"},
        {"name": "Analytics", "description": "Analytics and reporting"},
        {"name": "Admin", "description": "Administrative operations"},
    ]

    # Add servers
    openapi_schema["servers"] = [
        {"url": "http://localhost:8000", "description": "Development server"},
        {"url": "https://api.namaskah.app", "description": "Production server"},
    ]

    app.openapi_schema = openapi_schema
    return app.openapi_schema


def setup_openapi(app: FastAPI):

    """Setup OpenAPI documentation endpoints."""
    app.openapi = lambda: get_openapi_schema(app)
