#!/bin/bash
# Fix cards.py on server - restore backup and deploy correct version

SERVER="ubuntu@44.198.107.45"
API_DIR="/home/ubuntu/collectorstream-api"

echo "🔧 Fixing cards.py on server..."

# Step 1: Restore from backup
echo "📦 Restoring from backup..."
ssh $SERVER "cd $API_DIR && cp cards.py.backup cards.py"

# Step 2: Copy updated cards.py
echo "📤 Deploying updated cards.py..."
scp cards.py $SERVER:$API_DIR/cards.py

# Step 3: Verify file copied
echo "✅ Verifying deployment..."
ssh $SERVER "cd $API_DIR && ls -lh cards.py && tail -5 cards.py"

# Step 4: Restart service
echo "🔄 Restarting API service..."
ssh $SERVER "sudo systemctl restart collectorstream-api"

# Step 5: Wait and check status
sleep 3
echo "📊 Checking service status..."
ssh $SERVER "sudo systemctl status collectorstream-api --no-pager | head -15"

# Step 6: Test health endpoint
echo "🏥 Testing health endpoint..."
ssh $SERVER "curl -s http://localhost:8000/health | head -20"

echo ""
echo "✅ Deployment complete!"
echo ""
echo "Test the API:"
echo "  curl https://api.collectorstream.com/health"
echo ""
