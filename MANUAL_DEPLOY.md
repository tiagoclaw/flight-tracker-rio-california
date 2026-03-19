# 🚀 MANUAL RAILWAY DEPLOY - Step by Step

**Se os scripts automáticos não funcionarem, siga este guia manual.**

---

## 🎯 OPTION 1: Web Interface (MAIS FÁCIL)

### **Step 1: Acesse Railway**
1. Vá para: https://railway.app
2. **Login com GitHub** (use conta tiagoclaw)
3. **Authorize Railway** quando solicitado

### **Step 2: Novo Projeto**
1. Click: **"New Project"**  
2. Select: **"Deploy from GitHub repo"**
3. Choose: **`tiagoclaw/flight-tracker-rio-california`**
4. Click: **"Deploy Now"**

### **Step 3: Environment Variables (Opcional)**
Na aba **"Variables"** do projeto:
```
CHECK_INTERVAL_HOURS = 3
PRICE_DROP_THRESHOLD = 0.12
ALERT_EMAIL = tiago@example.com
TELEGRAM_CHAT_ID = 540464122
```

### **Step 4: Verificar Deploy**
1. Aba **"Deployments"** → Ver logs de build
2. Aguardar build completar (~2-5 minutos)
3. Aba **"Settings"** → **"Domains"** → Copiar URL
4. Testar: `curl https://your-url.up.railway.app/health`

---

## 🎯 OPTION 2: Railway CLI

### **Step 1: Instalar Railway CLI**

**macOS:**
```bash
brew install railway
```

**Windows:**
```bash
npm install -g @railway/cli
```

**Linux:**
```bash
curl -fsSL https://railway.app/install.sh | sh
```

### **Step 2: Login e Deploy**
```bash
# Login
railway login

# Clone o repo (se ainda não tem)
git clone https://github.com/tiagoclaw/flight-tracker-rio-california.git
cd flight-tracker-rio-california

# Inicializar projeto Railway
railway init

# Configurar variáveis (opcional)
railway variables set CHECK_INTERVAL_HOURS=3
railway variables set PRICE_DROP_THRESHOLD=0.12
railway variables set ALERT_EMAIL=seu-email@gmail.com

# Deploy
railway up
```

### **Step 3: Verificar**
```bash
# Ver logs
railway logs -f

# Ver status
railway status

# Obter URL do serviço
railway domain

# Testar health check
curl $(railway domain)/health
```

---

## 🎯 OPTION 3: GitHub Actions (AUTOMÁTICO)

### **Criar Workflow File:**
`.github/workflows/railway-deploy.yml`

```yaml
name: Deploy to Railway

on:
  push:
    branches: [ main ]
  workflow_dispatch:

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Install Railway CLI
        run: |
          curl -fsSL https://railway.app/install.sh | sh
          echo "$HOME/.railway/bin" >> $GITHUB_PATH
      
      - name: Deploy to Railway
        env:
          RAILWAY_TOKEN: ${{ secrets.RAILWAY_TOKEN }}
        run: |
          railway up --detach
```

**Setup:**
1. Railway Dashboard → **Settings** → **Tokens** → Generate
2. GitHub repo → **Settings** → **Secrets** → Add `RAILWAY_TOKEN`
3. Push para `main` branch → Auto-deploy

---

## ⚠️ TROUBLESHOOTING

### **Problem: Build Failed**
**Logs mostram erro de Docker:**
```bash
# Ver logs detalhados
railway logs --deployment-id=<deployment-id>

# Verificar Dockerfile
cat Dockerfile

# Rebuild manual
railway up --detach
```

### **Problem: Health Check Failed**
**Service starts mas health check falha:**
```bash
# Check port configuration
railway variables set PORT=8000

# Ver logs runtime
railway logs -f

# Test locally
docker build -t flight-tracker .
docker run -p 8000:8000 flight-tracker
curl localhost:8000/health
```

### **Problem: Variables Not Set**
**Environment variables não estão carregando:**
```bash
# Listar variables atuais
railway variables

# Set novamente
railway variables set CHECK_INTERVAL_HOURS=3
railway variables set DATABASE_URL=sqlite:///data/flights.db

# Restart service
railway up --detach
```

### **Problem: Out of Memory**
**Railway free tier tem 512MB limit:**
```bash
# Check memory usage nos logs
railway logs | grep -i "memory\|oom"

# Optimize Docker build
# Add to Dockerfile:
# RUN pip install --no-cache-dir -r requirements.txt
```

---

## 🎊 EXPECTED SUCCESS

### **Build Logs Should Show:**
```
==> Building with Docker
==> Using Dockerfile: Dockerfile
Step 1/8 : FROM python:3.12-slim
Step 2/8 : RUN apt-get update && apt-get install -y gcc curl
Step 3/8 : WORKDIR /app  
Step 4/8 : COPY requirements.txt .
Step 5/8 : RUN pip install --no-cache-dir -r requirements.txt
Step 6/8 : COPY . .
Step 7/8 : RUN mkdir -p /app/data
Step 8/8 : CMD ["python", "standalone_monitor.py"]
==> Build completed successfully
==> Deployment started
```

### **Runtime Logs Should Show:**
```
🛫 STANDALONE FLIGHT MONITOR - Rio to California
📍 4 routes: GIG/SDU → LAX/SFO  
⏰ 24/7 monitoring with smart alerts
🚨 Price drop detection & notifications

Monitor initialized - 4 routes, check every 3h
🛫 FLIGHT MONITOR STARTING - Rio to California
🎯 Starting cycle #1
🔄 Starting monitoring cycle...
🔍 Checking Rio Galeão → Los Angeles
Generated 11 flights for GIG-LAX on 2026-04-03
✅ Cycle complete: 43 flights, 0 alerts (15.2s)
😴 Sleeping 3h until next cycle...
```

### **Health Check Should Return:**
```json
{
  "status": "healthy",
  "service": "flight-tracker-rio-california",
  "timestamp": "2026-03-19T10:15:00.000Z", 
  "routes": ["GIG-LAX", "GIG-SFO", "SDU-LAX", "SDU-SFO"]
}
```

---

## 🎯 FINAL VERIFICATION

### **Dashboard Check:**
1. **Railway Dashboard:** https://railway.app/dashboard
2. **Project Status:** Should show "Deployed" with green dot
3. **Resource Usage:** Should show minimal CPU/RAM usage
4. **Logs:** Should show monitoring cycles every 3 hours

### **Service Check:**
1. **URL Access:** Your service should have a Railway URL
2. **Health Endpoint:** `/health` should return JSON status
3. **Database:** SQLite file should be created in `/data/`
4. **Monitoring:** Logs should show flight generation every 3h

---

## 🛫 SUCCESS = 24/7 RIO-CALIFORNIA FLIGHT MONITORING!

**When everything works:**
- ✅ Service running 24/7 on Railway
- ✅ Monitoring 4 routes every 3 hours
- ✅ Generating ~160 realistic flights per cycle
- ✅ Detecting price drops and logging alerts
- ✅ Building historical database automatically
- ✅ Health checks passing for uptime monitoring

**🎊 Result: Automated Rio-California flight price intelligence!**