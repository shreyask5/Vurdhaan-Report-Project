# Quick Start Guide - Firebase + Projects Dashboard

## 🚀 5-Minute Setup

### 1. Replace Dashboard Component
```bash
cd frontend/src/pages
mv Dashboard.tsx DashboardOld.tsx
mv DashboardNew.tsx Dashboard.tsx
```

### 2. Install Frontend Dependencies
```bash
cd frontend
npm install firebase date-fns
```

### 3. Configure Firebase

#### Get Firebase Credentials
1. Go to https://console.firebase.google.com/
2. Create/select your project
3. **Authentication** → Enable "Email/Password"
4. **Authentication** → Settings → Authorized Domains → Add `tools.vurdhaan.com`
5. **Firestore Database** → Create database (Start in production mode)
6. **Project Settings** → Your apps → Add Web App
7. Copy the Firebase config values

#### Backend Config
Create `github/Vurdhaan-Report-Project/.env`:
```env
FIREBASE_PROJECT_ID=your-project-id
FIREBASE_CREDENTIALS_PATH=./serviceAccountKey.json
CORS_ORIGINS=https://tools.vurdhaan.com
FLASK_ENV=production
SECRET_KEY=<run: python -c "import secrets; print(secrets.token_hex(32))">
OPENAI_API_KEY=sk-your-key
HOST=0.0.0.0
PORT=5002
```

#### Frontend Config
Create `frontend/.env`:
```env
VITE_API_BASE_URL=https://tools.vurdhaan.com/api
VITE_FIREBASE_API_KEY=AIzaSy...
VITE_FIREBASE_AUTH_DOMAIN=your-project.firebaseapp.com
VITE_FIREBASE_PROJECT_ID=your-project-id
VITE_FIREBASE_STORAGE_BUCKET=your-project.appspot.com
VITE_FIREBASE_MESSAGING_SENDER_ID=123456789
VITE_FIREBASE_APP_ID=1:123:web:abc123
```

### 4. Download Service Account Key
1. Firebase Console → Project Settings → Service Accounts
2. Click "Generate New Private Key"
3. Save as `serviceAccountKey.json` in project root

### 5. Install Backend Dependencies
```bash
pip install -r requirements.txt
```

### 6. Run the Application

**Terminal 1 - Backend:**
```bash
python app5.py
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

---

## ✅ Test the Flow

1. **Sign Up**
   - Go to http://localhost:3000
   - Click "Sign Up"
   - Create account with email/password
   - Login

2. **Create Project**
   - Go to Dashboard → Projects tab
   - Click "Create Project"
   - Enter name: "Test Project"
   - Toggle "Enable AI Chat" → ON
   - Toggle "Save Files on Server" → OFF
   - Click "Create Project"

3. **Verify AI Chat Button**
   - Project card should show "Open Chat" button ✅
   - Turn off "Enable AI Chat" in settings
   - "Open Chat" button should disappear ❌
   - Shows message: "💡 Enable AI Chat in settings..."

4. **Upload CSV**
   - Click "Upload CSV"
   - Select file, set dates
   - Upload and validate

5. **Use AI Chat**
   - If AI chat enabled and file uploaded
   - Click "Open Chat"
   - Ask: "How many flights in total?"

6. **Generate Report**
   - Click "Generate CORSIA Report"
   - Downloads Excel file

---

## 🔧 Troubleshooting

### "Blocked request. This host is not allowed"
**Already Fixed!** ✅ `vite.config.ts` updated with allowed hosts

### Firebase Auth Errors
```bash
# Check .env files exist
ls .env frontend/.env

# Verify Firebase config
grep FIREBASE frontend/.env
```

### API Errors
```bash
# Check backend is running
curl http://localhost:5002/api/health

# Should return:
# {"status":"healthy","version":"5.0.0"}
```

### CORS Errors
```bash
# Update backend .env
echo 'CORS_ORIGINS=http://localhost:3000,https://tools.vurdhaan.com' >> .env
```

---

## 📦 Production Deployment

See `DOMAIN_SETUP.md` for complete deployment guide including:
- Nginx configuration
- SSL setup with Let's Encrypt
- Systemd service
- Firestore security rules
- Monitoring

---

## 🎯 Key Features

### Project Creation
- ✅ Name + description
- ✅ Toggle: Enable AI Chat
- ✅ Toggle: Save Files on Server
- ✅ Creates via API → app5.py

### Conditional Chat Button
```typescript
// Shows ONLY if ai_chat_enabled === true
{project.ai_chat_enabled && project.has_file && (
  <Button>Open Chat</Button>
)}
```

### Backend Protection
```python
# In app5.py - prevents unauthorized access
if not project.get('ai_chat_enabled'):
    return jsonify({'error': 'AI chat not enabled'}), 403
```

---

## 📄 Files Created

- ✅ `app5.py` - Secure API backend
- ✅ `middleware/auth.py` - Firebase auth
- ✅ `middleware/rate_limit.py` - Rate limiting
- ✅ `middleware/validation.py` - Input validation
- ✅ `services/firebase_service.py` - Firestore ops
- ✅ `services/project_service.py` - Business logic
- ✅ `services/storage_service.py` - File storage
- ✅ `models/project.py` - Data models
- ✅ `frontend/src/contexts/AuthContext.tsx` - Real Firebase auth
- ✅ `frontend/src/services/firebase.ts` - Firebase config
- ✅ `frontend/src/services/api.ts` - API client
- ✅ `frontend/src/components/projects/CreateProjectDialog.tsx`
- ✅ `frontend/src/components/projects/ProjectCard.tsx`
- ✅ `frontend/src/pages/DashboardNew.tsx`

---

## 🎉 You're Ready!

All code is complete and ready to use. Just:
1. Configure Firebase
2. Update .env files
3. Run the app
4. Test the flow

**Happy coding! 🚀**
