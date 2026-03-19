# 🚀 DEPLOY INSTRUCTIONS - Railway

**Flight Tracker Rio-California** está pronto para deploy 24/7!

---

## 🎯 DEPLOY NO RAILWAY (RECOMENDADO)

### **Step 1: Acesse Railway**
1. **Vá para:** https://railway.app
2. **Login com GitHub** (use a conta tiagoclaw)

### **Step 2: Criar Novo Projeto**
1. **Click:** "New Project"
2. **Select:** "Deploy from GitHub repo"
3. **Choose:** `tiagoclaw/flight-tracker-rio-california`
4. **Confirm deployment**

### **Step 3: Configurar Environment Variables**
Na aba **Variables** do projeto Railway:

```env
# Monitoring Configuration
CHECK_INTERVAL_HOURS=3
PRICE_DROP_THRESHOLD=0.12
USE_MOCK_SCRAPER=true

# Database
DATABASE_URL=sqlite:///data/flights.db

# Notifications
ALERT_EMAIL=seu-email@gmail.com
TELEGRAM_CHAT_ID=540464122

# Optional: Real Telegram Bot (if you want notifications)
TELEGRAM_BOT_TOKEN=your_bot_token_here
```

### **Step 4: Deploy**
- Railway detecta `Dockerfile` automaticamente
- Deploy acontece automaticamente após configuração
- **Health check:** Disponível em `https://your-app.up.railway.app/health`

---

## ✅ VERIFICAÇÃO DEPLOY

### **Health Check**
```bash
curl https://your-railway-url/health
# Expected: {"status": "healthy", "service": "flight-tracker"}
```

### **Logs de Monitoramento**
No Railway dashboard → **Deployments** → **View Logs**:
```
🛫 FLIGHT TRACKER RIO-CALIFORNIA - PRODUCTION
📍 Routes: Rio (GIG/SDU) → California (LAX/SFO)
⏰ Monitoring: 24/7 price tracking
🚨 Alerts: Email + Telegram

🚀 Starting flight monitoring service...
🔄 Starting cycle #1
🔍 Checking Rio Galeão → Los Angeles
✅ Found 11 flights, cheapest: R$ 2,606.22 (Delta Air Lines)
😴 Sleeping for 3 hours...
```

---

## 🔧 CONFIGURAÇÕES AVANÇADAS

### **1. Intervalo de Monitoramento**
```env
CHECK_INTERVAL_HOURS=6    # Check every 6 hours (slower, less resource usage)
CHECK_INTERVAL_HOURS=2    # Check every 2 hours (faster, more alerts)
```

### **2. Threshold de Alertas**
```env
PRICE_DROP_THRESHOLD=0.10    # Alert on 10% price drop (more sensitive)
PRICE_DROP_THRESHOLD=0.20    # Alert on 20% price drop (less sensitive)
```

### **3. Dados Reais vs Mock**
```env
USE_MOCK_SCRAPER=false       # Try real scraping (may fail due to bot protection)
USE_MOCK_SCRAPER=true        # Use realistic mock data (always works)
```

### **4. Notification Setup**
```env
# Email (SMTP)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# Telegram Bot
TELEGRAM_BOT_TOKEN=123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11
TELEGRAM_CHAT_ID=540464122
```

---

## 🎊 O QUE ACONTECE APÓS DEPLOY

### **Monitoramento Automático:**
- ✅ **Check a cada 3 horas:** 4 rotas Rio-California
- ✅ **Múltiplas datas:** 2-8 semanas à frente, trips de 6 dias
- ✅ **Price tracking:** Histórico armazenado em SQLite
- ✅ **Smart alerts:** Só notifica em quedas significativas (12%+)

### **Exemplo de Funcionamento:**
```
Cycle #1: 09:00 - Check all routes
  GIG-LAX (Apr 30): R$ 3,200 (12 flights)
  GIG-SFO (May 15): R$ 3,400 (8 flights)
  SDU-LAX (May 01): R$ 3,600 (10 flights)
  SDU-SFO (May 16): R$ 3,800 (9 flights)

Cycle #2: 12:00 - Price drop detected!
  🚨 ALERT: GIG-LAX dropped 15% to R$ 2,720
  📧 Email sent to: your-email@gmail.com
  📱 Telegram notification sent

Cycle #3: 15:00 - Continue monitoring...
```

### **Database Growth:**
- **~100 flights/day** stored
- **30 days = ~3,000 records**
- **SQLite size: ~500KB/month**
- **Railway free tier: Plenty of storage**

---

## 🔍 TROUBLESHOOTING

### **Problem: Deploy Failed**
**Solution:**
1. Check Railway logs for errors
2. Verify Dockerfile syntax
3. Ensure GitHub repo is public

### **Problem: No Flight Data**
**Expected with mock data** - this is normal and intended.
**Real scraping** may be blocked by anti-bot protection.

### **Problem: No Alerts**
**Cause:** No significant price drops yet.
**Solution:** Lower `PRICE_DROP_THRESHOLD` to 0.05 (5%) for testing.

### **Problem: Health Check Fails**
**Solution:**
1. Check port 8000 is exposed
2. Verify prod_start.py is running
3. Check Railway service logs

---

## 💰 RAILWAY COST ESTIMATE

### **Hobby Plan (FREE):**
- ✅ **$5/month credit** included
- ✅ **Enough for this service** (~$2-3/month usage)
- ✅ **512MB RAM, 1 vCPU** (sufficient)
- ✅ **1GB storage** (plenty for SQLite)

### **Pro Plan ($20/month):**
- ✅ **Better uptime guarantees**
- ✅ **More resources** if needed
- ✅ **Priority support**

---

## 🎯 NEXT STEPS APÓS DEPLOY

### **Week 1: Validate System**
1. **Monitor logs** - verify cycles running
2. **Test alerts** - lower threshold temporarily
3. **Check database** - confirm data storage

### **Week 2: Real Data Integration**
1. **Try real scraping** - set `USE_MOCK_SCRAPER=false`
2. **Add proxy rotation** if needed
3. **Consider paid APIs** (Amadeus, Skyscanner)

### **Week 3: User Experience**
1. **Web dashboard** for price visualization
2. **Mobile notifications** via Push API
3. **Email templates** with better formatting

### **Week 4: Scaling**
1. **Add more routes** (Rio-Europe, Rio-US East Coast)
2. **Machine learning** price prediction
3. **User management** system

---

## 🛫 READY FOR TAKEOFF!

**✅ TUDO PRONTO PARA DEPLOY:**

**🔗 Repository:** https://github.com/tiagoclaw/flight-tracker-rio-california  
**🐳 Docker:** Production-ready Dockerfile  
**⚙️ Config:** Railway.json with health checks  
**🔄 Monitor:** 24/7 flight price tracking  
**🚨 Alerts:** Email + Telegram notifications  
**📊 Database:** SQLite with historical data  

**🚀 DEPLOY NOW:** 
1. Railway.app → New Project → GitHub → tiagoclaw/flight-tracker-rio-california
2. Set environment variables  
3. Deploy automatically happens
4. Health check: `your-app.up.railway.app/health`

**🎊 RESULTADO:** Sistema de monitoramento de preços Rio-California operando 24/7 com alertas inteligentes!**