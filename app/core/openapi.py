"""OpenAPI/Swagger documentation configuration."""

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi


def get_openapi_schema(app: FastAPI) -> dict:
    """Generate OpenAPI schema for API documentation."""
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title="Namaskah SMS Verification API",
        version="2.4.0",
        description="SMS Verification Platform with Multi-Provider Support",
        routes=app.routes,
    )

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
            "name": "X-API-Key",
            "description": "API key for programmatic access",
        },
    }

    app.openapi_schema = openapi_schema
    return app.openapi_schema
