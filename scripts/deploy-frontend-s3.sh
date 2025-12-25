#!/bin/bash
# Deploy ui-mobile frontend to S3 with proper cache headers

set -e

S3_BUCKET="${S3_BUCKET:-}"  # Must be set
REGION="${AWS_REGION:-us-east-1}"

if [ -z "$S3_BUCKET" ]; then
    echo "ERROR: S3_BUCKET must be set"
    echo "Usage: S3_BUCKET='your-bucket-name' ./scripts/deploy-frontend-s3.sh"
    exit 1
fi

echo "=== Deploying Frontend to S3 ==="
echo "Bucket: $S3_BUCKET"
echo "Region: $REGION"
echo ""

# Change to ui-mobile directory
cd "$(dirname "$0")/../ui-mobile"

# Check if directory exists
if [ ! -d "." ]; then
    echo "ERROR: ui-mobile directory not found"
    exit 1
fi

echo "=== Uploading files with cache headers ==="

# Upload index.html with no-cache headers
echo "Uploading index.html (no-cache)..."
aws s3 cp index.html "s3://$S3_BUCKET/index.html" \
    --cache-control "no-cache, no-store, must-revalidate" \
    --content-type "text/html" \
    --region "$REGION"

# Upload HTML files with no-cache
for html_file in *.html merchant/*.html wallet/*.html; do
    if [ -f "$html_file" ]; then
        echo "Uploading $html_file (no-cache)..."
        aws s3 cp "$html_file" "s3://$S3_BUCKET/$html_file" \
            --cache-control "no-cache, no-store, must-revalidate" \
            --content-type "text/html" \
            --region "$REGION"
    fi
done

# Upload CSS files with long cache (they have version query strings)
echo "Uploading CSS files..."
aws s3 sync css/ "s3://$S3_BUCKET/css/" \
    --cache-control "max-age=31536000, immutable" \
    --content-type "text/css" \
    --region "$REGION" \
    --delete

# Upload JS files with long cache
echo "Uploading JS files..."
aws s3 sync js/ "s3://$S3_BUCKET/js/" \
    --cache-control "max-age=31536000, immutable" \
    --content-type "application/javascript" \
    --region "$REGION" \
    --delete

# Upload assets with long cache
echo "Uploading assets..."
aws s3 sync assets/ "s3://$S3_BUCKET/assets/" \
    --cache-control "max-age=31536000, immutable" \
    --region "$REGION" \
    --delete

# Upload other static files
echo "Uploading other files..."
aws s3 cp manifest.json "s3://$S3_BUCKET/manifest.json" \
    --cache-control "no-cache" \
    --content-type "application/manifest+json" \
    --region "$REGION"

aws s3 cp manifest.webmanifest "s3://$S3_BUCKET/manifest.webmanifest" \
    --cache-control "no-cache" \
    --content-type "application/manifest+json" \
    --region "$REGION"

aws s3 cp sw.js "s3://$S3_BUCKET/sw.js" \
    --cache-control "no-cache" \
    --content-type "application/javascript" \
    --region "$REGION"

echo ""
echo "=== Upload Complete ==="
echo "Frontend deployed to: s3://$S3_BUCKET"
echo ""
echo "Next steps:"
echo "1. Create CloudFront distribution pointing to this bucket"
echo "2. Update backend ALLOWED_ORIGINS with CloudFront domain"
echo "3. Update ui-mobile/index.html with App Runner URL meta tag"


