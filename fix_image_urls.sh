#!/bin/bash
# Quick fix for image URL issue in CollectorStream API

echo "Fixing image URL issue..."

# Backup the original file
cp api/images.py api/images.py.backup

# Apply the fix
sed -i.bak 's|return f"/uploads/{filename}"|# Return absolute URL with API base\n    api_base = os.environ.get("API_BASE_URL", "https://api.collectorstream.com")\n    return f"{api_base}/uploads/{filename}"|' api/images.py

echo "Fix applied! Original backed up to api/images.py.backup"
echo ""
echo "Now restart your API service:"
echo "  sudo systemctl restart collectorstream-api"
echo "  OR"
echo "  pm2 restart collectorstream-api"
