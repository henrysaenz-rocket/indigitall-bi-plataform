# Technical Integration Guide
## inDigital Analytics Platform

**Prepared for:** inDigital Development Team
**Prepared by:** Abstract Studio
**Version:** 1.0
**Date:** December 2025

---

## Overview

This guide explains how to integrate the Abstract Studio Analytics Platform into the inDigital CRM. The integration requires minimal development effort from your team—approximately **1-2 days of work**.

### What You'll Implement

| Task | Effort | Description |
|------|--------|-------------|
| Token endpoint | 2-4 hours | Generate JWT tokens for authentication |
| Embed iframe | 1-2 hours | Add analytics iframe to your UI |
| API credentials | 1 hour | Provide API access for data sync |
| Testing | 2-4 hours | Verify integration works |

### What We Handle

- Platform hosting and maintenance
- Data synchronization from your APIs
- AI chat and visualization engine
- Multi-tenant security
- All updates and improvements

---

## Prerequisites

Before starting integration:

- [ ] Partnership agreement signed
- [ ] API documentation shared with Abstract Studio
- [ ] Shared secret key exchanged (for JWT signing)
- [ ] Staging environment access provided

---

## Step 1: Implement Token Endpoint

### 1.1 Overview

Your backend needs to generate a signed JWT token when users access the Analytics feature. This token tells our platform who the user is and which tenant's data they should see.

### 1.2 Token Specification

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `tenant_id` | string | Yes | Unique identifier for the company/client |
| `user_id` | string | Yes | User's email or unique ID |
| `user_name` | string | No | Display name for the user |
| `partner_id` | string | Yes | Always `"indigital"` |
| `roles` | array | No | User roles (e.g., `["admin"]`, `["analyst"]`) |
| `iat` | integer | Yes | Issued at (Unix timestamp) |
| `exp` | integer | Yes | Expiration (Unix timestamp, max 2 hours) |

### 1.3 Implementation Examples

#### Node.js (Express)

```javascript
const jwt = require('jsonwebtoken');
const express = require('express');

const SHARED_SECRET = process.env.ABSTRACT_STUDIO_SHARED_SECRET; // We'll provide this

const app = express();

// Middleware to verify user is logged in
const requireAuth = require('./middleware/auth');

app.get('/api/analytics-token', requireAuth, (req, res) => {
  const user = req.user; // Your authenticated user object

  const token = jwt.sign(
    {
      tenant_id: user.companyId,      // The client's unique ID in your system
      user_id: user.email,
      user_name: user.fullName,
      partner_id: 'indigital',
      roles: user.roles || ['analyst'],
    },
    SHARED_SECRET,
    {
      expiresIn: '1h',  // Token valid for 1 hour
      algorithm: 'HS256'
    }
  );

  res.json({ token });
});
```

#### Python (Flask)

```python
import jwt
from datetime import datetime, timedelta
from flask import Flask, jsonify, g

SHARED_SECRET = os.environ.get('ABSTRACT_STUDIO_SHARED_SECRET')  # We'll provide this

app = Flask(__name__)

@app.route('/api/analytics-token')
@require_auth  # Your authentication decorator
def get_analytics_token():
    user = g.current_user  # Your authenticated user object

    payload = {
        'tenant_id': user.company_id,  # The client's unique ID
        'user_id': user.email,
        'user_name': user.full_name,
        'partner_id': 'indigital',
        'roles': user.roles or ['analyst'],
        'iat': datetime.utcnow(),
        'exp': datetime.utcnow() + timedelta(hours=1)
    }

    token = jwt.encode(payload, SHARED_SECRET, algorithm='HS256')

    return jsonify({'token': token})
```

#### PHP (Laravel)

```php
<?php

namespace App\Http\Controllers;

use Firebase\JWT\JWT;
use Illuminate\Http\Request;

class AnalyticsController extends Controller
{
    public function getToken(Request $request)
    {
        $user = $request->user();
        $secret = config('services.abstractstudio.shared_secret');

        $payload = [
            'tenant_id' => $user->company_id,
            'user_id' => $user->email,
            'user_name' => $user->name,
            'partner_id' => 'indigital',
            'roles' => $user->roles ?? ['analyst'],
            'iat' => time(),
            'exp' => time() + 3600,  // 1 hour
        ];

        $token = JWT::encode($payload, $secret, 'HS256');

        return response()->json(['token' => $token]);
    }
}
```

#### Java (Spring Boot)

```java
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.SignatureAlgorithm;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api")
public class AnalyticsController {

    @Value("${abstractstudio.shared-secret}")
    private String sharedSecret;

    @GetMapping("/analytics-token")
    public Map<String, String> getAnalyticsToken(@AuthenticationPrincipal User user) {

        Date now = new Date();
        Date expiration = new Date(now.getTime() + 3600000); // 1 hour

        String token = Jwts.builder()
            .claim("tenant_id", user.getCompanyId())
            .claim("user_id", user.getEmail())
            .claim("user_name", user.getFullName())
            .claim("partner_id", "indigital")
            .claim("roles", user.getRoles())
            .setIssuedAt(now)
            .setExpiration(expiration)
            .signWith(SignatureAlgorithm.HS256, sharedSecret.getBytes())
            .compact();

        return Map.of("token", token);
    }
}
```

### 1.4 Security Requirements

| Requirement | Implementation |
|-------------|----------------|
| HTTPS only | Endpoint must be served over HTTPS |
| Authentication | User must be logged in to get token |
| Rate limiting | Recommend 10 requests/minute per user |
| Secret rotation | Support for secret key rotation (notify us 48h before) |

### 1.5 Error Handling

Return appropriate HTTP status codes:

| Status | When |
|--------|------|
| `200 OK` | Token generated successfully |
| `401 Unauthorized` | User not authenticated |
| `403 Forbidden` | User doesn't have analytics access |
| `500 Internal Server Error` | Token generation failed |

---

## Step 2: Embed the Analytics iframe

### 2.1 Overview

Add an iframe to your application where you want the Analytics feature to appear. The iframe loads our platform with the user's token.

### 2.2 Basic Implementation

#### React

```jsx
import React, { useState, useEffect } from 'react';

const ANALYTICS_URL = 'https://analytics.abstractstudio.co';

function AnalyticsPage() {
  const [token, setToken] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function fetchToken() {
      try {
        const response = await fetch('/api/analytics-token', {
          credentials: 'include',  // Include auth cookies
        });

        if (!response.ok) {
          throw new Error('Failed to get analytics token');
        }

        const data = await response.json();
        setToken(data.token);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    }

    fetchToken();
  }, []);

  if (loading) {
    return <div className="loading">Loading Analytics...</div>;
  }

  if (error) {
    return <div className="error">Unable to load Analytics: {error}</div>;
  }

  return (
    <div className="analytics-container">
      <iframe
        src={`${ANALYTICS_URL}/?token=${token}`}
        title="Analytics"
        style={{
          width: '100%',
          height: 'calc(100vh - 60px)',  // Adjust based on your header
          border: 'none',
        }}
        allow="clipboard-write"  // For copy functionality
      />
    </div>
  );
}

export default AnalyticsPage;
```

#### Vue.js

```vue
<template>
  <div class="analytics-container">
    <div v-if="loading" class="loading">Loading Analytics...</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <iframe
      v-else
      :src="analyticsUrl"
      title="Analytics"
      class="analytics-iframe"
      allow="clipboard-write"
    />
  </div>
</template>

<script>
export default {
  name: 'AnalyticsPage',

  data() {
    return {
      token: null,
      loading: true,
      error: null,
      baseUrl: 'https://analytics.abstractstudio.co',
    };
  },

  computed: {
    analyticsUrl() {
      return `${this.baseUrl}/?token=${this.token}`;
    },
  },

  async mounted() {
    try {
      const response = await this.$http.get('/api/analytics-token');
      this.token = response.data.token;
    } catch (err) {
      this.error = 'Unable to load Analytics';
    } finally {
      this.loading = false;
    }
  },
};
</script>

<style scoped>
.analytics-container {
  width: 100%;
  height: calc(100vh - 60px);
}

.analytics-iframe {
  width: 100%;
  height: 100%;
  border: none;
}
</style>
```

#### Angular

```typescript
// analytics.component.ts
import { Component, OnInit } from '@angular/core';
import { DomSanitizer, SafeResourceUrl } from '@angular/platform-browser';
import { HttpClient } from '@angular/common/http';

@Component({
  selector: 'app-analytics',
  template: `
    <div class="analytics-container">
      <div *ngIf="loading" class="loading">Loading Analytics...</div>
      <div *ngIf="error" class="error">{{ error }}</div>
      <iframe
        *ngIf="iframeSrc"
        [src]="iframeSrc"
        title="Analytics"
        class="analytics-iframe"
        allow="clipboard-write"
      ></iframe>
    </div>
  `,
  styles: [`
    .analytics-container { width: 100%; height: calc(100vh - 60px); }
    .analytics-iframe { width: 100%; height: 100%; border: none; }
  `]
})
export class AnalyticsComponent implements OnInit {
  iframeSrc: SafeResourceUrl | null = null;
  loading = true;
  error: string | null = null;

  private baseUrl = 'https://analytics.abstractstudio.co';

  constructor(
    private http: HttpClient,
    private sanitizer: DomSanitizer
  ) {}

  ngOnInit() {
    this.http.get<{ token: string }>('/api/analytics-token').subscribe({
      next: (response) => {
        const url = `${this.baseUrl}/?token=${response.token}`;
        this.iframeSrc = this.sanitizer.bypassSecurityTrustResourceUrl(url);
        this.loading = false;
      },
      error: (err) => {
        this.error = 'Unable to load Analytics';
        this.loading = false;
      }
    });
  }
}
```

#### Plain JavaScript

```html
<!-- analytics.html -->
<div id="analytics-container">
  <div id="analytics-loading">Loading Analytics...</div>
  <div id="analytics-error" style="display: none;"></div>
  <iframe
    id="analytics-iframe"
    title="Analytics"
    style="display: none; width: 100%; height: calc(100vh - 60px); border: none;"
    allow="clipboard-write"
  ></iframe>
</div>

<script>
  const ANALYTICS_URL = 'https://analytics.abstractstudio.co';

  async function loadAnalytics() {
    const loading = document.getElementById('analytics-loading');
    const error = document.getElementById('analytics-error');
    const iframe = document.getElementById('analytics-iframe');

    try {
      const response = await fetch('/api/analytics-token', {
        credentials: 'include'
      });

      if (!response.ok) throw new Error('Failed to get token');

      const { token } = await response.json();

      iframe.src = `${ANALYTICS_URL}/?token=${token}`;
      iframe.style.display = 'block';
      loading.style.display = 'none';

    } catch (err) {
      loading.style.display = 'none';
      error.textContent = 'Unable to load Analytics: ' + err.message;
      error.style.display = 'block';
    }
  }

  loadAnalytics();
</script>
```

### 2.3 Styling Recommendations

```css
/* Recommended styles for analytics container */
.analytics-container {
  width: 100%;
  height: calc(100vh - var(--header-height, 60px));
  display: flex;
  flex-direction: column;
}

.analytics-iframe {
  flex: 1;
  width: 100%;
  border: none;
  background: #f5f5f5;  /* Loading background */
}

.analytics-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  font-size: 16px;
  color: #666;
}

.analytics-error {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #d32f2f;
  padding: 20px;
  text-align: center;
}

/* Mobile responsiveness */
@media (max-width: 768px) {
  .analytics-container {
    height: calc(100vh - var(--mobile-header-height, 50px));
  }
}
```

### 2.4 Content Security Policy

If you use CSP headers, add our domain to `frame-src`:

```
Content-Security-Policy: frame-src 'self' https://analytics.abstractstudio.co;
```

---

## Step 3: Token Refresh (Optional but Recommended)

### 3.1 Overview

Tokens expire after 1 hour. For longer sessions, implement token refresh to avoid interrupting users.

### 3.2 Implementation

```javascript
// Listen for token refresh requests from iframe
window.addEventListener('message', async (event) => {
  // Verify origin
  if (event.origin !== 'https://analytics.abstractstudio.co') return;

  if (event.data.type === 'TOKEN_REFRESH_REQUIRED') {
    try {
      // Get new token from your backend
      const response = await fetch('/api/analytics-token', {
        credentials: 'include'
      });
      const { token } = await response.json();

      // Send new token to iframe
      const iframe = document.getElementById('analytics-iframe');
      iframe.contentWindow.postMessage({
        type: 'TOKEN_REFRESH',
        token: token
      }, 'https://analytics.abstractstudio.co');

    } catch (error) {
      console.error('Token refresh failed:', error);
      // Optionally redirect to login
    }
  }
});
```

---

## Step 4: Provide API Access

### 4.1 What We Need

To sync data from your platform, we need:

| Item | Description | How to Provide |
|------|-------------|----------------|
| API base URL | Your API endpoint | e.g., `https://api.indigital.com/v1` |
| API credentials | Authentication for API access | OAuth app credentials or API key |
| Rate limit info | Requests per minute/hour | Documentation or verbal |
| Webhook URL (optional) | For real-time updates | We'll provide the URL |

### 4.2 Required API Endpoints

We need read access to these endpoints:

| Endpoint | Data | Sync Frequency |
|----------|------|----------------|
| `GET /users` | Customer/contact records | Every 15 min |
| `GET /events` | User activities/events | Every 15 min |
| `GET /transactions` | Purchase/transaction data | Every 15 min |
| `GET /campaigns` | Marketing campaigns | Every 1 hour |
| `GET /messages` | Communications sent | Every 15 min |

### 4.3 API Requirements

For efficient syncing, your APIs should support:

| Feature | Why We Need It |
|---------|----------------|
| Incremental queries | `?updated_since=2025-01-01T00:00:00Z` |
| Pagination | `?cursor=xxx` or `?page=1&limit=100` |
| Tenant filtering | `?tenant_id=xxx` or via auth context |

### 4.4 Webhook Integration (Optional)

For real-time data updates, configure webhooks to our endpoint:

```
POST https://api.abstractstudio.co/webhooks/indigital/{tenant_id}

Headers:
  X-Webhook-Signature: {HMAC signature}
  Content-Type: application/json

Body:
{
  "event": "user.created",
  "data": { ... },
  "timestamp": "2025-01-15T10:30:00Z"
}
```

We'll provide:
- Webhook URL
- Signature verification secret
- List of events we want to receive

---

## Step 5: Testing

### 5.1 Testing Checklist

#### Token Endpoint

- [ ] Endpoint returns 200 with valid JWT
- [ ] Token contains all required claims
- [ ] Token is properly signed
- [ ] Unauthenticated requests return 401
- [ ] Token expiration is set correctly

#### iframe Embedding

- [ ] iframe loads without errors
- [ ] User sees their company's data only
- [ ] No console errors related to CSP
- [ ] Works on desktop browsers (Chrome, Firefox, Safari, Edge)
- [ ] Works on mobile browsers
- [ ] Loading state displays correctly
- [ ] Error state displays correctly

#### Data Sync

- [ ] API credentials work
- [ ] Data appears in analytics within 15 minutes
- [ ] All entities sync correctly

### 5.2 Test Accounts

We'll provide test accounts for your staging environment:

| Tenant | User | Purpose |
|--------|------|---------|
| `test_tenant_a` | `user_a@test.com` | General testing |
| `test_tenant_b` | `user_b@test.com` | Multi-tenant verification |
| `test_admin` | `admin@indigital.com` | Partner admin testing |

### 5.3 Verification Steps

1. **Token Test:**
   ```bash
   curl -X GET https://your-api.com/api/analytics-token \
     -H "Cookie: your_auth_cookie=xxx"

   # Should return: {"token": "eyJ..."}
   ```

2. **Token Decode Test:**
   Go to [jwt.io](https://jwt.io) and paste your token to verify claims.

3. **iframe Test:**
   Open browser console and verify no errors when loading analytics.

4. **Data Test:**
   Ask a question like "How many contacts do I have?" and verify the count matches your database.

---

## Step 6: Go Live

### 6.1 Pre-Launch Checklist

- [ ] All tests passing in staging
- [ ] Production API credentials configured
- [ ] Production shared secret exchanged
- [ ] CSP headers updated for production
- [ ] Monitoring in place
- [ ] Support escalation path defined

### 6.2 Rollout Strategy

We recommend a phased rollout:

| Phase | Scope | Duration |
|-------|-------|----------|
| 1. Internal | Your team only | 1 week |
| 2. Pilot | 3-5 selected clients | 2 weeks |
| 3. Gradual | 25% of clients | 1 week |
| 4. Full | All clients | Ongoing |

### 6.3 Feature Flag (Recommended)

Control analytics access with a feature flag:

```javascript
// Example: Only show Analytics tab if enabled
function shouldShowAnalytics(tenant) {
  return tenant.features.includes('analytics')
    || tenant.plan === 'premium'
    || BETA_TENANTS.includes(tenant.id);
}
```

---

## Troubleshooting

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| "Invalid token" error | Wrong shared secret | Verify secret matches |
| "Token expired" | Token older than 1 hour | Implement token refresh |
| Blank iframe | CSP blocking | Add our domain to frame-src |
| "No data found" | Tenant ID mismatch | Verify tenant_id matches |
| CORS errors | Missing headers | Not applicable (iframe, not API) |
| Slow loading | Large initial data load | Expected on first load |

### Debug Mode

Add `?debug=true` to the iframe URL to see detailed error messages:

```
https://analytics.abstractstudio.co/?token=xxx&debug=true
```

### Getting Help

| Channel | Use For | Response Time |
|---------|---------|---------------|
| Slack #indigital-support | Quick questions | < 4 hours |
| Email: support@abstractstudio.ai | Detailed issues | < 24 hours |
| Emergency: [phone] | Production down | < 1 hour |

---

## Appendix

### A. JWT Libraries

| Language | Library |
|----------|---------|
| Node.js | `jsonwebtoken` |
| Python | `PyJWT` |
| PHP | `firebase/php-jwt` |
| Java | `io.jsonwebtoken:jjwt` |
| C# | `System.IdentityModel.Tokens.Jwt` |
| Go | `github.com/golang-jwt/jwt` |
| Ruby | `jwt` |

### B. Sample Token

```
Header:
{
  "alg": "HS256",
  "typ": "JWT"
}

Payload:
{
  "tenant_id": "acme_corp",
  "user_id": "maria@acmecorp.com",
  "user_name": "Maria Garcia",
  "partner_id": "indigital",
  "roles": ["analyst"],
  "iat": 1704067200,
  "exp": 1704070800
}

Signature:
HMACSHA256(
  base64UrlEncode(header) + "." + base64UrlEncode(payload),
  SHARED_SECRET
)
```

### C. Status Codes Reference

| Code | Meaning | Action |
|------|---------|--------|
| 200 | Success | Display analytics |
| 401 | Unauthorized | Redirect to login |
| 403 | Forbidden | Show "no access" message |
| 404 | Not found | Check URL |
| 429 | Rate limited | Wait and retry |
| 500 | Server error | Contact support |

### D. Contact Information

| Role | Name | Email |
|------|------|-------|
| Technical Lead | TBD | tech@abstractstudio.ai |
| Account Manager | TBD | account@abstractstudio.ai |
| Support | - | support@abstractstudio.ai |

---

*Questions? Reach out to your Abstract Studio contact or email support@abstractstudio.ai*
