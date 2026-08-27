"""
OpenAPI Configuration for Jadus Audit API

Centralizes OpenAPI schema tags, examples, and metadata
"""

# Tags for organizing endpoints
TAGS_METADATA = [
    {
        "name": "Agents",
        "description": "Enroll agents and manage agent information",
        "externalDocs": {
            "description": "Agent Management Guide",
            "url": "https://c2.internal/docs/agents",
        },
    },
    {
        "name": "Tasks",
        "description": "Create and retrieve audit tasks for agents",
    },
    {
        "name": "Results",
        "description": "Submit and retrieve audit results (encrypted)",
    },
    {
        "name": "Monitoring",
        "description": "System-wide monitoring and analytics",
    },
    {
        "name": "Health",
        "description": "Health checks and status endpoints",
    },
]

# OpenAPI server configuration
SERVERS = [
    {
        "url": "http://localhost:8000",
        "description": "Development server",
    },
    {
        "url": "https://api.c2.internal",
        "description": "Production server",
    },
]

# OpenAPI information
INFO = {
    "title": "Jadus Audit API",
    "description": """
## Overview

Jadus Audit API is a REST API for managing PowerShell audit agents in an enterprise environment.

### Key Features

- 🔐 **Secure Authentication**: UUID + API Key authentication per agent
- 🚦 **Rate Limiting**: Sliding window algorithm per agent per endpoint
- 📊 **Real-time Monitoring**: Dashboard with live agent statistics
- 🔒 **Encrypted Results**: AES-256-GCM encryption for sensitive audit data
- 📝 **Audit Logging**: JSON structured logging for compliance
- ⚡ **High Performance**: Sub-second response times for 1000+ agents

### Architecture

```
Agent (PowerShell)
    ↓
POST /api/enroll → Get agent_id + api_key
    ↓
POST /api/beacon → Heartbeat + get pending tasks
    ↓
Execute task locally
    ↓
POST /api/results → Submit encrypted results
    ↓
GET /api/monitoring/* → Admin dashboard (Vue.js)
```

### Authentication

All endpoints except `/api/enroll` require:
- `agent_id` + `api_key` in request body
- Headers with valid credentials

### Rate Limiting

Endpoints are rate limited per agent:
- `POST /api/enroll`: 5 requests/hour per host
- `POST /api/beacon`: 100 requests/hour per agent
- `POST /api/results`: 50 requests/hour per agent

Response includes:
- `X-RateLimit-Limit`: Maximum requests allowed
- `X-RateLimit-Remaining`: Requests remaining
- `X-RateLimit-Reset`: Timestamp when limit resets

Returns **HTTP 429** if limit exceeded.

### Encryption

All audit results are encrypted with AES-256-GCM:
- `result_encrypted`: Ciphertext (base64)
- `result_hash`: SHA-256 hash for searching
- `result_preview`: Safe preview for UI ("Output: 2500 bytes, 45 lines")

Only administrators with the `ENCRYPTION_KEY` can decrypt.

### Error Handling

All errors follow standard HTTP status codes:
- `400`: Bad Request (validation error)
- `401`: Unauthorized (invalid credentials)
- `404`: Not Found (resource doesn't exist)
- `409`: Conflict (resource already exists)
- `422`: Unprocessable Entity (invalid data format)
- `429`: Too Many Requests (rate limit exceeded)
- `500`: Internal Server Error

All error responses include a `detail` field with explanation.

### Examples

See [API_DOCUMENTATION.md](./API_DOCUMENTATION.md) for detailed examples.
""",
    "version": "1.0.0",
    "contact": {
        "name": "Jadus Audit Administrator",
        "email": "admin@c2.internal",
    },
    "license": {
        "name": "Internal Use Only",
    },
}
