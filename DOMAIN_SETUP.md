# Domain Setup Guide - tools.vurdhaan.com

## Configuration Checklist

### ✅ Already Done
- [x] Vite config updated with `allowedHosts`
- [x] .env.example updated with production domain

---

## 1. Firebase Configuration

### Add Authorized Domains

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Select your project
3. Navigate to **Authentication** → **Settings** → **Authorized domains**
4. Click **Add domain** and add:
   ```
   tools.vurdhaan.com
   ```

### Update CORS Settings (if using Firebase Storage)

1. Create `cors.json`:
```json
[
  {
    "origin": ["https://tools.vurdhaan.com"],
    "method": ["GET", "POST", "PUT", "DELETE"],
    "maxAgeSeconds": 3600
  }
]
```

2. Apply CORS settings:
```bash
gsutil cors set cors.json gs://your-bucket-name.appspot.com
```

---

## 2. Backend (.env) Configuration

Copy `.env.example` to `.env` and update:

```env
# PRODUCTION Settings
FLASK_ENV=production
HOST=0.0.0.0
PORT=5002

# CORS - Add your domain
CORS_ORIGINS=https://tools.vurdhaan.com

# Firebase
FIREBASE_PROJECT_ID=your-project-id
FIREBASE_CREDENTIALS_PATH=/path/to/serviceAccountKey.json

# Security
SECRET_KEY=<generate-random-key>

# OpenAI
OPENAI_API_KEY=sk-your-actual-key
```

**Generate SECRET_KEY:**
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

---

## 3. Frontend (.env) Configuration

Create `frontend/.env`:

```env
# Production API URL (your Flask backend)
VITE_API_BASE_URL=https://api.vurdhaan.com/api
# OR if backend is on same server:
# VITE_API_BASE_URL=https://tools.vurdhaan.com:5002/api

# Firebase Config (from Firebase Console → Project Settings → Web App)
VITE_FIREBASE_API_KEY=AIzaSy...
VITE_FIREBASE_AUTH_DOMAIN=your-project.firebaseapp.com
VITE_FIREBASE_PROJECT_ID=your-project-id
VITE_FIREBASE_STORAGE_BUCKET=your-project.appspot.com
VITE_FIREBASE_MESSAGING_SENDER_ID=123456789
VITE_FIREBASE_APP_ID=1:123:web:abc123
```

---

## 4. Nginx Reverse Proxy Setup (Ubuntu Server)

### Install Nginx
```bash
sudo apt update
sudo apt install nginx
```

### Configure SSL with Let's Encrypt
```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d tools.vurdhaan.com
```

### Nginx Configuration

Create `/etc/nginx/sites-available/vurdhaan-tools`:

```nginx
# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name tools.vurdhaan.com;
    return 301 https://$server_name$request_uri;
}

# HTTPS Frontend
server {
    listen 443 ssl http2;
    server_name tools.vurdhaan.com;

    # SSL certificates (managed by certbot)
    ssl_certificate /etc/letsencrypt/live/tools.vurdhaan.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/tools.vurdhaan.com/privkey.pem;

    # SSL settings
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;

    # Frontend (React build)
    root /var/www/vurdhaan-tools/dist;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    # API Proxy (to Flask backend)
    location /api/ {
        proxy_pass http://127.0.0.1:5002;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;

        # CORS headers (if needed)
        add_header Access-Control-Allow-Origin "https://tools.vurdhaan.com" always;
        add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS" always;
        add_header Access-Control-Allow-Headers "Authorization, Content-Type" always;

        # Preflight requests
        if ($request_method = 'OPTIONS') {
            return 204;
        }
    }

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api_limit:10m rate=60r/m;
    limit_req zone=api_limit burst=20;
}
```

### Enable Site
```bash
sudo ln -s /etc/nginx/sites-available/vurdhaan-tools /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

---

## 5. Deploy Backend (Flask app5.py)

### Using Systemd Service

Create `/etc/systemd/system/vurdhaan-api.service`:

```ini
[Unit]
Description=Vurdhaan Report API (app5.py)
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/var/www/vurdhaan-api
Environment="PATH=/var/www/vurdhaan-api/venv/bin"
ExecStart=/var/www/vurdhaan-api/venv/bin/gunicorn -w 4 -b 127.0.0.1:5002 app5:app
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### Start Service
```bash
sudo systemctl daemon-reload
sudo systemctl enable vurdhaan-api
sudo systemctl start vurdhaan-api
sudo systemctl status vurdhaan-api
```

---

## 6. Deploy Frontend (React)

### Build Frontend
```bash
cd frontend
npm run build
```

### Copy to Server
```bash
sudo mkdir -p /var/www/vurdhaan-tools
sudo cp -r dist/* /var/www/vurdhaan-tools/
sudo chown -R www-data:www-data /var/www/vurdhaan-tools
```

---

## 7. Firewall Setup

```bash
# Allow HTTP/HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Allow SSH (if not already)
sudo ufw allow 22/tcp

# Enable firewall
sudo ufw enable
```

---

## 8. DNS Configuration

Make sure your DNS has an A record:

```
Type: A
Name: tools
Value: <your-server-ip>
TTL: 3600
```

Or CNAME if using subdomain:
```
Type: CNAME
Name: tools
Value: vurdhaan.com
```

---

## 9. Testing Checklist

After deployment, test:

- [ ] `https://tools.vurdhaan.com` loads frontend
- [ ] Firebase authentication works
- [ ] Can create project
- [ ] Can upload CSV file
- [ ] API calls work (check browser console)
- [ ] SSL certificate is valid
- [ ] Redirects HTTP → HTTPS
- [ ] CORS headers correct
- [ ] Rate limiting works

### Test API Endpoint
```bash
curl https://tools.vurdhaan.com/api/health
# Should return: {"status":"healthy","version":"5.0.0"}
```

---

## 10. Monitoring & Logs

### View Backend Logs
```bash
# Systemd service logs
sudo journalctl -u vurdhaan-api -f

# Application logs
tail -f /var/www/vurdhaan-api/logs/app.log
```

### View Nginx Logs
```bash
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log
```

---

## 11. Update Your Actual .env Files

**Backend (.env):**
```bash
cd /var/www/vurdhaan-api
cp .env.example .env
nano .env
# Update with real values
```

**Frontend (.env):**
```bash
cd frontend
nano .env
# Update with real Firebase config
```

**Then rebuild frontend:**
```bash
npm run build
```

---

## Quick Deployment Commands

```bash
# Deploy backend
cd /var/www/vurdhaan-api
git pull
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart vurdhaan-api

# Deploy frontend
cd /var/www/vurdhaan-api/frontend
git pull
npm install
npm run build
sudo cp -r dist/* /var/www/vurdhaan-tools/
```

---

## Security Notes

1. **Never commit** `.env` files to git
2. **Use HTTPS** everywhere (enforced by Nginx config above)
3. **Rotate secrets** regularly
4. **Monitor logs** for suspicious activity
5. **Keep updated**: `sudo apt update && sudo apt upgrade`
6. **Backup** Firebase service account key securely

---

## Troubleshooting

### CORS Errors
- Check `CORS_ORIGINS` in backend .env
- Verify Nginx CORS headers
- Check browser console for exact error

### Firebase Auth Errors
- Verify domain added to Firebase authorized domains
- Check Firebase config in frontend .env
- Ensure API key is correct

### API Not Reachable
- Check backend is running: `sudo systemctl status vurdhaan-api`
- Check Nginx proxy: `sudo nginx -t`
- Check firewall: `sudo ufw status`

### SSL Certificate Issues
```bash
# Renew certificate
sudo certbot renew --dry-run
sudo certbot renew
```

---

Need help? Check logs first:
```bash
# Backend
sudo journalctl -u vurdhaan-api -n 100

# Nginx
tail -f /var/log/nginx/error.log
```
