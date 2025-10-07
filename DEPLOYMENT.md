# Deployment Guide - Vurdhaan Report Project (app5.py)

## Overview

This guide covers deploying the secure Flask API backend (app5.py) with Firebase authentication, React frontend, and all security features.

---

## Architecture

```
┌─────────────────┐
│  React Frontend │ ──────> Firebase Auth (ID Token)
│   (localhost:   │
│      3000)      │
└────────┬────────┘
         │
         │ HTTPS + Bearer Token
         ▼
┌─────────────────┐
│  Flask API      │ ──────> Firebase Admin SDK (Token Verification)
│   (app5.py)     │ ──────> Firestore (Project Data)
│   Port 5002     │ ──────> Local Storage (Files)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  DuckDB + AI    │
│  (Chat/SQL)     │
└─────────────────┘
```

---

## Prerequisites

### 1. Firebase Setup

1. Create a Firebase project at [Firebase Console](https://console.firebase.google.com/)
2. Enable **Authentication** → Email/Password
3. Enable **Firestore Database**
4. Generate service account key:
   - Project Settings → Service Accounts → Generate New Private Key
   - Download JSON file → Save as `serviceAccountKey.json`
5. Get Web App credentials:
   - Project Settings → Your Apps → Web App
   - Copy config values

### 2. Python Environment

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Node.js Environment

```bash
cd frontend
npm install
```

---

## Configuration

### Backend (.env)

Copy `.env.example` to `.env` and configure:

```env
# Firebase
FIREBASE_PROJECT_ID=your-project-id
FIREBASE_CREDENTIALS_PATH=./serviceAccountKey.json

# API
SECRET_KEY=random-secret-key-here
FLASK_ENV=development
HOST=0.0.0.0
PORT=5002

# CORS (add your React app URL)
CORS_ORIGINS=http://localhost:3000,http://localhost:5173

# OpenAI
OPENAI_API_KEY=sk-your-key

# Storage
UPLOAD_FOLDER=./uploads
```

### Frontend (.env)

Create `frontend/.env`:

```env
VITE_API_BASE_URL=http://localhost:5002/api
VITE_FIREBASE_API_KEY=your-api-key
VITE_FIREBASE_AUTH_DOMAIN=your-project.firebaseapp.com
VITE_FIREBASE_PROJECT_ID=your-project-id
VITE_FIREBASE_STORAGE_BUCKET=your-project.appspot.com
VITE_FIREBASE_MESSAGING_SENDER_ID=123456789
VITE_FIREBASE_APP_ID=1:123456789:web:abc123
```

---

## Security Checklist

### Before Production

- [ ] Change `SECRET_KEY` to random value (use `openssl rand -hex 32`)
- [ ] Set `FLASK_ENV=production`
- [ ] Enable HTTPS/TLS (use reverse proxy like Nginx)
- [ ] Use Firebase Workload Identity instead of service account JSON
- [ ] Set strict CORS origins (only your production domain)
- [ ] Enable Redis for rate limiting (not in-memory)
- [ ] Set up WAF/API Gateway
- [ ] Configure firewall rules
- [ ] Enable audit logging
- [ ] Set up monitoring (Sentry, Prometheus)
- [ ] Regular security audits

### Firestore Security Rules

```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // Projects - user can only access their own
    match /projects/{projectId} {
      allow read, write: if request.auth != null
        && resource.data.owner_uid == request.auth.uid;
      allow create: if request.auth != null
        && request.resource.data.owner_uid == request.auth.uid;
    }

    // Users - can only read/write own document
    match /users/{userId} {
      allow read, write: if request.auth != null
        && request.auth.uid == userId;
    }
  }
}
```

---

## Running the Application

### Development

**Terminal 1 - Backend:**
```bash
python app5.py
# Runs on http://localhost:5002
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
# Runs on http://localhost:3000
```

### Production

**Backend (using Gunicorn):**
```bash
gunicorn -w 4 -b 0.0.0.0:5002 app5:app
```

**Frontend (build):**
```bash
cd frontend
npm run build
# Serve dist/ with Nginx or similar
```

---

## API Endpoints

### Authentication
- `POST /api/auth/verify` - Verify Firebase token
- `GET /api/auth/me` - Get current user

### Projects
- `GET /api/projects` - List projects
- `POST /api/projects` - Create project
- `GET /api/projects/<id>` - Get project
- `PUT /api/projects/<id>` - Update project
- `DELETE /api/projects/<id>` - Delete project

### File Operations
- `POST /api/projects/<id>/upload` - Upload CSV
- `GET /api/projects/<id>/download/<type>` - Download CSV
- `POST /api/projects/<id>/report` - Generate report

### Chat (requires AI enabled)
- `POST /api/projects/<id>/chat/initialize` - Init session
- `POST /api/projects/<id>/chat/query` - Send query

---

## Rate Limits

- Global: 120 req/min per IP
- Authenticated: 60 req/min per user
- Upload: 10 per hour
- Chat: 30 per hour
- Report: 5 per hour

---

## Testing

### Backend
```bash
pytest tests/
```

### Frontend
```bash
cd frontend
npm test
```

### Manual Testing
1. Sign up via React app
2. Create project with toggles
3. Upload CSV file
4. Enable AI chat → Test chat
5. Generate report
6. Test file download

---

## Monitoring

### Logs
```bash
# View app logs
tail -f logs/app.log

# View errors only
grep "ERROR" logs/app.log
```

### Metrics
- Track API response times
- Monitor rate limit hits
- Watch Firebase quota
- Check file storage size

---

## Troubleshooting

### Firebase Auth Errors
- Verify `FIREBASE_CREDENTIALS_PATH` is correct
- Check service account has Firestore permissions
- Ensure Firebase Auth is enabled

### CORS Errors
- Add frontend URL to `CORS_ORIGINS`
- Check browser console for exact origin
- Verify `OPTIONS` preflight succeeds

### Rate Limit Issues
- Use Redis in production (not memory)
- Adjust limits in middleware/rate_limit.py
- Check IP forwarding if behind proxy

### File Upload Fails
- Check `UPLOAD_FOLDER` exists and writable
- Verify `MAX_CONTENT_LENGTH` setting
- Ensure adequate disk space

---

## Migration from app4.py

1. **Keep app4.py running** on port 5001
2. **Start app5.py** on port 5002
3. **Update React frontend** to use app5 API
4. **Gradual rollout**: Allow users to choose
5. **Monitor both** for a transition period
6. **Deprecate app4.py** after full migration

---

## Production Deployment (Example with Nginx)

### Nginx Configuration
```nginx
server {
    listen 443 ssl http2;
    server_name api.yourdomain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location /api/ {
        proxy_pass http://127.0.0.1:5002;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Rate limiting
        limit_req zone=api_limit burst=10;
    }
}
```

---

## Security Best Practices

1. **Never commit**:
   - `.env` file
   - `serviceAccountKey.json`
   - `uploads/` directory

2. **Always use**:
   - HTTPS in production
   - Strong `SECRET_KEY`
   - Latest dependencies
   - Firewall rules

3. **Regular tasks**:
   - Update dependencies
   - Rotate secrets
   - Review logs
   - Audit permissions

---

## Support & Resources

- Firebase Docs: https://firebase.google.com/docs
- Flask Security: https://flask.palletsprojects.com/en/latest/security/
- React Best Practices: https://react.dev/

---

## License

[Your License Here]
