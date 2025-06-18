# 🔌 VaultView API Documentation

## Overview

VaultView provides a comprehensive REST API for domain security monitoring. All API endpoints return JSON responses and require proper authentication.

## Base URL

```
http://localhost:5000/api/v1
```

## Authentication

Most API endpoints require authentication. Include your session cookie or API token in requests.

### Session Authentication
```bash
# Login first to get session cookie
curl -X POST http://localhost:5000/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=your_username&password=your_password" \
  -c cookies.txt

# Use session cookie for subsequent requests
curl -X GET http://localhost:5000/api/v1/domains \
  -b cookies.txt
```

## Endpoints

### 🔐 Authentication

#### POST /auth/login
Authenticate a user and create a session.

**Request Body:**
```json
{
  "username": "string",
  "password": "string"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Login successful",
  "user": {
    "id": 1,
    "username": "string",
    "email": "string"
  }
}
```

#### POST /auth/register
Register a new user account.

**Request Body:**
```json
{
  "username": "string",
  "email": "string",
  "password": "string",
  "confirm_password": "string"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Registration successful"
}
```

#### POST /auth/logout
Logout and destroy the current session.

**Response:**
```json
{
  "success": true,
  "message": "Logout successful"
}
```

### 🔍 Domain Scanning

#### POST /scan/ssl
Scan a domain for SSL certificate information.

**Request Body:**
```json
{
  "domain": "example.com"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "domain": "example.com",
    "subject": "CN=example.com",
    "issuer": "CN=DigiCert Inc, O=DigiCert Inc, C=US",
    "valid_until": "2024-12-31T23:59:59Z",
    "is_valid": true,
    "days_until_expiry": 45,
    "serial_number": "1234567890abcdef",
    "version": 3
  }
}
```

#### POST /scan/dns
Scan a domain for DNS records.

**Request Body:**
```json
{
  "domain": "example.com"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "domain": "example.com",
    "records": {
      "A": ["93.184.216.34"],
      "AAAA": ["2606:2800:220:1:248:1893:25c8:1946"],
      "MX": [
        {
          "priority": 10,
          "server": "mail.example.com"
        }
      ],
      "NS": ["ns1.example.com", "ns2.example.com"],
      "TXT": ["v=spf1 include:_spf.google.com ~all"],
      "CAA": [
        {
          "flags": 0,
          "tag": "issue",
          "value": "letsencrypt.org",
          "description": "Allow Let's Encrypt to issue certificates"
        }
      ]
    }
  }
}
```

#### POST /scan/whois
Get WHOIS information for a domain.

**Request Body:**
```json
{
  "domain": "example.com"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "domain": "example.com",
    "registrar": "ICANN",
    "creation_date": "1995-08-14T04:00:00Z",
    "expiration_date": "2024-08-13T04:00:00Z",
    "updated_date": "2023-08-14T04:00:00Z",
    "status": "clientTransferProhibited",
    "name_servers": ["ns1.example.com", "ns2.example.com"],
    "emails": ["admin@example.com"]
  }
}
```

#### POST /scan/blacklist
Check if a domain is blacklisted.

**Request Body:**
```json
{
  "domain": "example.com"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "domain": "example.com",
    "blacklists": {
      "spamhaus": {
        "name": "Spamhaus",
        "listed": false,
        "status": "Not Listed",
        "description": "Spamhaus DNSBL",
        "response_ip": null
      },
      "surbl": {
        "name": "SURBL",
        "listed": false,
        "status": "Not Listed",
        "description": "SURBL DNSBL",
        "response_ip": null
      }
    }
  }
}
```

#### POST /scan/email
Perform email diagnostics on a domain.

**Request Body:**
```json
{
  "domain": "example.com"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "domain": "example.com",
    "overall_score": 85,
    "score_level": "Good",
    "mx_records": [
      {
        "priority": 10,
        "server": "mail.example.com",
        "resolved": "192.168.1.1"
      }
    ],
    "security_records": {
      "spf": {
        "found": true,
        "status": "Valid",
        "record": "v=spf1 include:_spf.google.com ~all"
      },
      "dkim": {
        "found": true,
        "status": "Valid",
        "count": 1
      },
      "dmarc": {
        "found": true,
        "status": "Valid",
        "record": "v=DMARC1; p=quarantine; rua=mailto:dmarc@example.com"
      }
    },
    "smtp_tests": {
      "mail.example.com": {
        "ip": "192.168.1.1",
        "tests": {
          "connection": {
            "status": "Connected"
          },
          "starttls": {
            "status": "Supported"
          }
        }
      }
    },
    "recommendations": [
      "Consider implementing stricter DMARC policy",
      "Add backup MX records"
    ]
  }
}
```

### 📊 Bulk Operations

#### POST /scan/bulk
Perform bulk scanning on multiple domains.

**Request Body:**
```json
{
  "domains": ["example.com", "google.com", "github.com"],
  "scan_type": "SSL"
}
```

**Response:**
```json
{
  "success": true,
  "results": [
    {
      "domain": "example.com",
      "status": "success",
      "scan_type": "SSL",
      "data": {
        "subject": "CN=example.com",
        "issuer": "CN=DigiCert Inc",
        "valid_until": "2024-12-31T23:59:59Z",
        "is_valid": true,
        "days_until_expiry": 45
      }
    },
    {
      "domain": "google.com",
      "status": "success",
      "scan_type": "SSL",
      "data": {
        "subject": "CN=*.google.com",
        "issuer": "CN=GTS CA 1C3",
        "valid_until": "2024-12-31T23:59:59Z",
        "is_valid": true,
        "days_until_expiry": 45
      }
    }
  ]
}
```

### 📈 History & Reports

#### GET /history
Get scan history for the authenticated user.

**Query Parameters:**
- `page` (optional): Page number (default: 1)
- `per_page` (optional): Items per page (default: 20)
- `scan_type` (optional): Filter by scan type
- `domain` (optional): Filter by domain

**Response:**
```json
{
  "success": true,
  "data": {
    "results": [
      {
        "id": 1,
        "domain": "example.com",
        "result_type": "SSL",
        "timestamp": "2024-01-15T10:30:00Z",
        "status": "success"
      }
    ],
    "pagination": {
      "page": 1,
      "per_page": 20,
      "total": 100,
      "pages": 5
    }
  }
}
```

#### GET /history/{id}
Get detailed scan result by ID.

**Response:**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "domain": "example.com",
    "result_type": "SSL",
    "result_data": {
      "subject": "CN=example.com",
      "issuer": "CN=DigiCert Inc",
      "valid_until": "2024-12-31T23:59:59Z",
      "is_valid": true,
      "days_until_expiry": 45
    },
    "timestamp": "2024-01-15T10:30:00Z",
    "user_id": 1
  }
}
```

### 🔔 Notifications

#### GET /notifications
Get user notifications.

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "type": "ssl_expiry",
      "message": "SSL certificate for example.com expires in 5 days",
      "domain": "example.com",
      "timestamp": "2024-01-15T10:30:00Z",
      "read": false
    }
  ]
}
```

#### POST /notifications/{id}/read
Mark a notification as read.

**Response:**
```json
{
  "success": true,
  "message": "Notification marked as read"
}
```

## Error Responses

All endpoints may return error responses in the following format:

```json
{
  "success": false,
  "error": "Error message",
  "code": "ERROR_CODE"
}
```

### Common Error Codes

- `AUTH_REQUIRED`: Authentication required
- `INVALID_CREDENTIALS`: Invalid username or password
- `DOMAIN_INVALID`: Invalid domain format
- `SCAN_FAILED`: Scan operation failed
- `RATE_LIMITED`: Too many requests
- `SERVER_ERROR`: Internal server error

## Rate Limiting

API requests are rate-limited to prevent abuse:
- **Authenticated users**: 100 requests per minute
- **Unauthenticated users**: 10 requests per minute

Rate limit headers are included in responses:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1642248600
```

## Pagination

List endpoints support pagination with the following query parameters:
- `page`: Page number (default: 1)
- `per_page`: Items per page (default: 20, max: 100)

Pagination metadata is included in responses:
```json
{
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 100,
    "pages": 5,
    "has_next": true,
    "has_prev": false
  }
}
```

## SDK Examples

### Python
```python
import requests

class VaultViewAPI:
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url
        self.session = requests.Session()
    
    def login(self, username, password):
        response = self.session.post(f"{self.base_url}/login", data={
            "username": username,
            "password": password
        })
        return response.json()
    
    def scan_ssl(self, domain):
        response = self.session.post(f"{self.base_url}/api/v1/scan/ssl", json={
            "domain": domain
        })
        return response.json()
    
    def bulk_scan(self, domains, scan_type):
        response = self.session.post(f"{self.base_url}/api/v1/scan/bulk", json={
            "domains": domains,
            "scan_type": scan_type
        })
        return response.json()

# Usage
api = VaultViewAPI()
api.login("username", "password")
result = api.scan_ssl("example.com")
print(result)
```

### JavaScript
```javascript
class VaultViewAPI {
    constructor(baseURL = 'http://localhost:5000') {
        this.baseURL = baseURL;
    }
    
    async login(username, password) {
        const response = await fetch(`${this.baseURL}/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: `username=${encodeURIComponent(username)}&password=${encodeURIComponent(password)}`,
            credentials: 'include'
        });
        return response.json();
    }
    
    async scanSSL(domain) {
        const response = await fetch(`${this.baseURL}/api/v1/scan/ssl`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ domain }),
            credentials: 'include'
        });
        return response.json();
    }
    
    async bulkScan(domains, scanType) {
        const response = await fetch(`${this.baseURL}/api/v1/scan/bulk`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ domains, scan_type: scanType }),
            credentials: 'include'
        });
        return response.json();
    }
}

// Usage
const api = new VaultViewAPI();
api.login('username', 'password')
    .then(() => api.scanSSL('example.com'))
    .then(result => console.log(result));
```

## WebSocket API

For real-time updates, VaultView also provides WebSocket endpoints:

```javascript
const ws = new WebSocket('ws://localhost:5000/ws');

ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    console.log('Received:', data);
};

// Subscribe to SSL alerts
ws.send(JSON.stringify({
    type: 'subscribe',
    channel: 'ssl_alerts'
}));
```

## Support

For API support and questions:
- **Documentation**: [docs/](docs/)
- **Issues**: [GitHub Issues](https://github.com/yourusername/vaultview/issues)
- **Email**: api-support@vaultview.com 