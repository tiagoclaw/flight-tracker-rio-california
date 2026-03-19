#!/bin/bash

echo "🚀 RAILWAY DEPLOY AUTOMATION SCRIPT"
echo "=================================="
echo ""
echo "🎯 Repository: tiagoclaw/flight-tracker-rio-california"
echo "🐳 Docker: Production ready"
echo "⚙️ Config: railway.json configured"
echo ""

# Check if railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo "📦 Installing Railway CLI..."
    
    # Install Railway CLI
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        brew install railway
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        curl -fsSL https://railway.app/install.sh | sh
        export PATH=$PATH:/home/$USER/.railway/bin
    else
        echo "❌ Unsupported OS. Please install Railway CLI manually:"
        echo "   https://docs.railway.app/deploy/builds#railway-cli"
        exit 1
    fi
fi

echo "✅ Railway CLI ready"
echo ""

# Login to Railway
echo "🔐 STEP 1: Railway Login"
echo "Please login to Railway when prompted..."
railway login

if [ $? -ne 0 ]; then
    echo "❌ Railway login failed"
    exit 1
fi

echo "✅ Logged in to Railway"
echo ""

# Create new project
echo "🏗️ STEP 2: Creating Railway Project"
echo "Project name: flight-tracker-rio-california"

# Initialize project in current directory
railway init

if [ $? -ne 0 ]; then
    echo "❌ Failed to initialize Railway project"
    echo "💡 Try manually: railway init"
    exit 1
fi

echo "✅ Railway project initialized"
echo ""

# Set environment variables
echo "⚙️ STEP 3: Setting Environment Variables"

railway variables set CHECK_INTERVAL_HOURS=3
railway variables set PRICE_DROP_THRESHOLD=0.12
railway variables set DATABASE_URL=sqlite:///data/flights.db
railway variables set USE_MOCK_SCRAPER=true
railway variables set LOG_LEVEL=INFO

# Optional: Set user-specific variables
echo ""
echo "🔧 OPTIONAL: Set your email for alerts (press Enter to skip)"
read -p "Email address: " user_email
if [ ! -z "$user_email" ]; then
    railway variables set ALERT_EMAIL="$user_email"
    echo "✅ Alert email set to: $user_email"
fi

echo ""
echo "🔧 OPTIONAL: Set Telegram Chat ID for alerts (press Enter to skip)"
read -p "Telegram Chat ID: " telegram_id
if [ ! -z "$telegram_id" ]; then
    railway variables set TELEGRAM_CHAT_ID="$telegram_id"
    echo "✅ Telegram alerts set to: $telegram_id"
fi

echo "✅ Environment variables configured"
echo ""

# Deploy to Railway
echo "🚀 STEP 4: Deploying to Railway"
echo "This will build Docker container and start the service..."

railway up

if [ $? -ne 0 ]; then
    echo "❌ Deploy failed"
    echo ""
    echo "🔧 TROUBLESHOOTING:"
    echo "1. Check Railway dashboard: https://railway.app/dashboard"
    echo "2. View build logs: railway logs"
    echo "3. Check Dockerfile: railway shell"
    echo ""
    exit 1
fi

echo "🎉 DEPLOY SUCCESS!"
echo ""

# Get service URL
echo "🌐 Getting service URL..."
service_url=$(railway domain)

if [ ! -z "$service_url" ]; then
    echo "✅ Service URL: $service_url"
    echo ""
    
    # Test health check
    echo "🏥 Testing health check..."
    if curl -f -s "$service_url/health" > /dev/null; then
        echo "✅ Health check PASSED"
        echo ""
        echo "🎊 DEPLOYMENT COMPLETE!"
        echo "🛫 Flight tracker is now monitoring Rio-California routes 24/7!"
        echo ""
        echo "📊 Service Details:"
        echo "   URL: $service_url"
        echo "   Health: $service_url/health"
        echo "   Logs: railway logs"
        echo "   Variables: railway variables"
        echo ""
    else
        echo "⚠️ Health check failed, but service might be starting..."
        echo "💡 Check logs: railway logs"
    fi
else
    echo "⚠️ Could not get service URL"
    echo "💡 Check Railway dashboard: https://railway.app/dashboard"
fi

echo "🎯 NEXT STEPS:"
echo "1. Monitor logs: railway logs -f"
echo "2. Check dashboard: https://railway.app/dashboard"  
echo "3. Wait for first monitoring cycle (3 hours)"
echo "4. Verify alerts are working"
echo ""
echo "🛫 Happy flight tracking!"