#!/bin/bash
#
# Deploy CollectorStream API to AWS Lightsail
# Updates the backend with improved multi-model card identification
#

set -e  # Exit on error

SERVER="ubuntu@api.collectorstream.com"
REMOTE_DIR="/home/ubuntu/collectorstream-api"

echo "🚀 Deploying CollectorStream API to production..."
echo ""

# Step 1: Copy updated files
echo "📦 Copying files to server..."
rsync -avz --progress \
  --exclude 'venv' \
  --exclude '__pycache__' \
  --exclude '*.pyc' \
  --exclude '.env' \
  --exclude 'data/*.db' \
  . $SERVER:$REMOTE_DIR/

# Step 2: Update environment variables on server
echo ""
echo "🔧 Updating environment variables..."
ssh $SERVER << 'EOF'
cd /home/ubuntu/collectorstream-api

# Check if .env exists, if not copy from example
if [ ! -f .env ]; then
    echo "Creating .env from example..."
    cp .env.example .env
fi

# Source the parent .env if it exists (contains API keys)
if [ -f ../.env ]; then
    echo "Loading API keys from parent .env..."
    source ../.env

    # Update .env with API keys
    if [ ! -z "$ANTHROPIC_API_KEY" ]; then
        grep -q "ANTHROPIC_API_KEY=" .env && \
            sed -i "s/ANTHROPIC_API_KEY=.*/ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY/" .env || \
            echo "ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY" >> .env
        echo "✅ Added ANTHROPIC_API_KEY"
    fi

    if [ ! -z "$OPENROUTER_API_KEY" ]; then
        grep -q "OPENROUTER_API_KEY=" .env && \
            sed -i "s/OPENROUTER_API_KEY=.*/OPENROUTER_API_KEY=$OPENROUTER_API_KEY/" .env || \
            echo "OPENROUTER_API_KEY=$OPENROUTER_API_KEY" >> .env
        echo "✅ Added OPENROUTER_API_KEY"
    fi

    if [ ! -z "$XIMILAR_API_KEY" ]; then
        grep -q "XIMILAR_API_KEY=" .env && \
            sed -i "s/XIMILAR_API_KEY=.*/XIMILAR_API_KEY=$XIMILAR_API_KEY/" .env || \
            echo "XIMILAR_API_KEY=$XIMILAR_API_KEY" >> .env
        echo "✅ Added XIMILAR_API_KEY"
    fi
fi
EOF

# Step 3: Install dependencies and restart service
echo ""
echo "📚 Installing dependencies and restarting service..."
ssh $SERVER << 'EOF'
cd /home/ubuntu/collectorstream-api

# Activate virtual environment
source venv/bin/activate

# Install/update dependencies
pip install -r requirements.txt --quiet

# Restart the API service
sudo systemctl restart collectorstream-api

# Check status
sleep 2
sudo systemctl status collectorstream-api --no-pager
EOF

echo ""
echo "✅ Deployment complete!"
echo ""
echo "🔍 Test the API:"
echo "   curl https://api.collectorstream.com/health"
echo ""
echo "📊 View logs:"
echo "   ssh $SERVER 'sudo journalctl -u collectorstream-api -f'"
echo ""
