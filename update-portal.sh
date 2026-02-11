#!/bin/bash
# Update CollectorStream portal to use new API

echo "Downloading current portal pages from S3..."
cd /tmp
mkdir -p collectorstream-portal && cd collectorstream-portal

# Download all pages
for page in index.html login.html signup.html portfolio.html profile.html dashboard.html; do
    curl -s "https://collectorstream.com/$page" > "$page" 2>/dev/null
    if [ -s "$page" ]; then
        echo "✓ Downloaded $page"
    else
        echo "✗ $page not found"
        rm -f "$page"
    fi
done

echo ""
echo "Updating API endpoints..."

# Update API endpoint in all HTML files
find . -name "*.html" -type f -exec sed -i.bak \
    's|https://16bs8nqbr8.execute-api.us-east-1.amazonaws.com|https://api.collectorstream.com/v1|g' {} \;

# Update auth/me to auth/validate
find . -name "*.html" -type f -exec sed -i.bak2 \
    's|/auth/me"|/auth/validate"|g' {} \;

# Update portfolio endpoint to cards endpoint
find . -name "*.html" -type f -exec sed -i.bak3 \
    's|/portfolio"|/cards?page=1\&per_page=100"|g' {} \;

echo "✓ API endpoints updated"
echo ""
echo "Files ready for upload:"
ls -lh *.html 2>/dev/null | grep -v ".bak"

echo ""
echo "To deploy, upload these files to your S3 bucket:"
echo "  aws s3 cp . s3://YOUR-BUCKET-NAME/ --recursive --exclude '*.bak*'"
