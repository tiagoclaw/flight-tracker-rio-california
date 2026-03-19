@echo off
echo 🚀 RAILWAY DEPLOY AUTOMATION SCRIPT - Windows
echo ============================================
echo.
echo 🎯 Repository: tiagoclaw/flight-tracker-rio-california
echo 🐳 Docker: Production ready
echo ⚙️ Config: railway.json configured
echo.

REM Check if railway CLI is installed
railway --version >nul 2>&1
if %errorlevel% neq 0 (
    echo 📦 Railway CLI not found. Installing...
    echo Please install Railway CLI manually from:
    echo https://docs.railway.app/deploy/builds#railway-cli
    echo.
    echo For Windows: npm install -g @railway/cli
    echo.
    pause
    exit /b 1
)

echo ✅ Railway CLI ready
echo.

echo 🔐 STEP 1: Railway Login
echo Please login to Railway when prompted...
railway login

if %errorlevel% neq 0 (
    echo ❌ Railway login failed
    pause
    exit /b 1
)

echo ✅ Logged in to Railway
echo.

echo 🏗️ STEP 2: Creating Railway Project
railway init

if %errorlevel% neq 0 (
    echo ❌ Failed to initialize Railway project
    echo 💡 Try manually: railway init
    pause
    exit /b 1
)

echo ✅ Railway project initialized
echo.

echo ⚙️ STEP 3: Setting Environment Variables
railway variables set CHECK_INTERVAL_HOURS=3
railway variables set PRICE_DROP_THRESHOLD=0.12
railway variables set DATABASE_URL=sqlite:///data/flights.db
railway variables set USE_MOCK_SCRAPER=true
railway variables set LOG_LEVEL=INFO

echo.
echo 🔧 OPTIONAL: Set your email for alerts (press Enter to skip)
set /p user_email="Email address: "
if not "%user_email%"=="" (
    railway variables set ALERT_EMAIL=%user_email%
    echo ✅ Alert email set to: %user_email%
)

echo.
echo 🔧 OPTIONAL: Set Telegram Chat ID (press Enter to skip)
set /p telegram_id="Telegram Chat ID: "
if not "%telegram_id%"=="" (
    railway variables set TELEGRAM_CHAT_ID=%telegram_id%
    echo ✅ Telegram alerts set to: %telegram_id%
)

echo ✅ Environment variables configured
echo.

echo 🚀 STEP 4: Deploying to Railway
echo This will build Docker container and start the service...
railway up

if %errorlevel% neq 0 (
    echo ❌ Deploy failed
    echo.
    echo 🔧 TROUBLESHOOTING:
    echo 1. Check Railway dashboard: https://railway.app/dashboard
    echo 2. View build logs: railway logs
    echo 3. Check container status: railway status
    echo.
    pause
    exit /b 1
)

echo 🎉 DEPLOY SUCCESS!
echo.

echo 🌐 Getting service information...
railway status

echo.
echo 🎊 DEPLOYMENT COMPLETE!
echo 🛫 Flight tracker should now be monitoring Rio-California routes!
echo.
echo 📊 Useful Commands:
echo   railway logs -f          : View live logs
echo   railway variables        : View environment variables
echo   railway status           : Check service status
echo   railway open             : Open in browser
echo.
echo 🎯 Check Railway dashboard: https://railway.app/dashboard
echo.
pause