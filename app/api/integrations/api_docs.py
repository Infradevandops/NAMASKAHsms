"""API documentation endpoints."""
from fastapi import APIRouter, Depends
from app.core.dependencies import get_current_user_id

router = APIRouter(prefix="/api/docs", tags=["documentation"])


@router.get("/endpoints")
async def get_api_endpoints(user_id: str = Depends(get_current_user_id)):
    """Get all API endpoints documentation."""
    return {
        "success": True,
        "endpoints": {
            "verification": {
                "create": {
                    "method": "POST",
                    "path": "/api/verify/create-real",
                    "description": "Create SMS verification",
                    "auth": "required",
                    "params": {
                        "service": "string (required)",
                        "area_code": "string (optional)",
                        "carrier": "string (optional)",
                    },
                },
                "status": {
                    "method": "GET",
                    "path": "/api/verify/{id}/status-real",
                    "description": "Get verification status",
                    "auth": "required",
                },
                "balance": {
                    "method": "GET",
                    "path": "/api/verify/balance",
                    "description": "Get account balance",
                    "auth": "required",
                },
            },
            "rentals": {
                "create": {
                    "method": "POST",
                    "path": "/api/rentals/create-real",
                    "description": "Create phone rental",
                    "auth": "required",
                    "params": {
                        "service": "string (required)",
                        "duration_days": "integer (1-365)",
                        "renewable": "boolean",
                    },
                },
                "list": {
                    "method": "GET",
                    "path": "/api/rentals/active",
                    "description": "Get active rentals",
                    "auth": "required",
                },
                "extend": {
                    "method": "POST",
                    "path": "/api/rentals/{id}/extend",
                    "description": "Extend rental duration",
                    "auth": "required",
                    "params": {"duration_days": "integer (1-365)"},
                },
            },
            "sms": {
                "inbox": {
                    "method": "GET",
                    "path": "/api/sms/inbox",
                    "description": "Get SMS messages",
                    "auth": "required",
                    "params": {"limit": "integer", "offset": "integer"},
                },
                "sync": {
                    "method": "POST",
                    "path": "/api/sms/inbox/sync",
                    "description": "Sync messages from API",
                    "auth": "required",
                },
                "mark_read": {
                    "method": "POST",
                    "path": "/api/sms/{id}/mark-read",
                    "description": "Mark message as read",
                    "auth": "required",
                },
            },
            "billing": {
                "initialize": {
                    "method": "POST",
                    "path": "/api/billing/paystack/initialize",
                    "description": "Initialize payment",
                    "auth": "required",
                    "params": {"amount": "float", "email": "string"},
                },
                "transactions": {
                    "method": "GET",
                    "path": "/api/billing/transactions",
                    "description": "Get transaction history",
                    "auth": "required",
                },
            },
            "wake_requests": {
                "create": {
                    "method": "POST",
                    "path": "/api/wake-requests/create",
                    "description": "Create wake request",
                    "auth": "required",
                    "params": {"rental_id": "string"},
                },
                "estimate": {
                    "method": "POST",
                    "path": "/api/wake-requests/estimate",
                    "description": "Estimate usage window",
                    "auth": "required",
                    "params": {"rental_id": "string"},
                },
            },
            "api_keys": {
                "generate": {
                    "method": "POST",
                    "path": "/api/keys/generate",
                    "description": "Generate new API key",
                    "auth": "required",
                },
                "list": {
                    "method": "GET",
                    "path": "/api/keys/list",
                    "description": "List API keys",
                    "auth": "required",
                },
                "revoke": {
                    "method": "POST",
                    "path": "/api/keys/{id}/revoke",
                    "description": "Revoke API key",
                    "auth": "required",
                },
            },
        },
    }


@router.get("/examples")
async def get_code_examples(user_id: str = Depends(get_current_user_id)):
    """Get code examples for API usage."""
    return {
        "success": True,
        "examples": {
            "python": {
                "create_verification": """
import requests

headers = {"Authorization": "Bearer YOUR_TOKEN"}
response = requests.post(
    "https://api.namaskah.app/api/verify/create-real",
    headers=headers,
    json={"service": "telegram"}
)
print(response.json())
                """,
                "get_balance": """

headers = {"Authorization": "Bearer YOUR_TOKEN"}
response = requests.get(
    "https://api.namaskah.app/api/verify/balance",
    headers=headers
)
print(response.json())
                """,
            },
            "javascript": {
                "create_verification": """
const token = localStorage.getItem('token');
const response = await fetch('https://api.namaskah.app/api/verify/create-real', {
    method: 'POST',
    headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({ service: 'telegram' })
});
console.log(await response.json());
                """,
                "get_balance": """
const token = localStorage.getItem('token');
const response = await fetch('https://api.namaskah.app/api/verify/balance', {
    headers: { 'Authorization': `Bearer ${token}` }
});
console.log(await response.json());
                """,
            },
            "curl": {
                "create_verification": """
curl -X POST https://api.namaskah.app/api/verify/create-real \\
  -H "Authorization: Bearer YOUR_TOKEN" \\
  -H "Content-Type: application/json" \\
  -d '{"service": "telegram"}'
                """,
                "get_balance": """
curl https://api.namaskah.app/api/verify/balance \\
  -H "Authorization: Bearer YOUR_TOKEN"
                """,
            },
        },
    }


@router.get("/authentication")
async def get_auth_docs(user_id: str = Depends(get_current_user_id)):
    """Get authentication documentation."""
    return {
        "success": True,
        "authentication": {
            "method": "Bearer Token",
            "header": "Authorization: Bearer YOUR_TOKEN",
            "how_to_get_token": "POST /api/auth/login with email and password",
            "token_expiry": "24 hours",
            "refresh": "Login again to get new token",
        },
    }


@router.get("/errors")
async def get_error_codes(user_id: str = Depends(get_current_user_id)):
    """Get error codes documentation."""
    return {
        "success": True,
        "errors": {
            "400": "Bad Request - Invalid parameters",
            "401": "Unauthorized - Invalid or missing token",
            "404": "Not Found - Resource not found",
            "429": "Rate Limited - Too many requests",
            "500": "Server Error - Internal error",
        },
    }
