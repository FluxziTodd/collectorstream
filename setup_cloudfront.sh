#!/bin/bash
# Run this AFTER updating GoDaddy nameservers and waiting for SSL cert validation
# It adds the custom domain to CloudFront and creates the Route 53 alias records

set -e
PROFILE=fluxzi
CERT_ARN="arn:aws:acm:us-east-1:573051981405:certificate/49ce49e7-02c8-4aa4-be0b-438ddf8492c1"
DIST_ID="E26VWZLVN1SVFJ"
HOSTED_ZONE_ID="Z0005387PZUL5V0AV7BF"
CF_HOSTED_ZONE="Z2FDTNDATAQYW2"  # CloudFront's fixed hosted zone ID

echo "Checking SSL certificate status..."
STATUS=$(aws acm describe-certificate --certificate-arn "$CERT_ARN" --profile "$PROFILE" --query 'Certificate.Status' --output text)
echo "Certificate status: $STATUS"

if [ "$STATUS" != "ISSUED" ]; then
    echo "Certificate not yet issued. Make sure GoDaddy nameservers are updated to:"
    echo "  ns-624.awsdns-14.net"
    echo "  ns-1925.awsdns-48.co.uk"
    echo "  ns-1160.awsdns-17.org"
    echo "  ns-186.awsdns-23.com"
    echo ""
    echo "Then wait for DNS propagation and re-run this script."
    exit 1
fi

echo "SSL certificate is valid. Updating CloudFront distribution..."

# Get current config
aws cloudfront get-distribution-config --id "$DIST_ID" --profile "$PROFILE" > /tmp/cf-config.json
ETAG=$(python3 -c "import json; print(json.load(open('/tmp/cf-config.json'))['ETag'])")

# Update config to add aliases and SSL cert
python3 -c "
import json
with open('/tmp/cf-config.json') as f:
    data = json.load(f)
config = data['DistributionConfig']
config['Aliases'] = {
    'Quantity': 2,
    'Items': ['collectorstream.com', 'www.collectorstream.com']
}
config['ViewerCertificate'] = {
    'ACMCertificateArn': '$CERT_ARN',
    'SSLSupportMethod': 'sni-only',
    'MinimumProtocolVersion': 'TLSv1.2_2021'
}
config['DefaultCacheBehavior']['ViewerProtocolPolicy'] = 'redirect-to-https'
with open('/tmp/cf-config-updated.json', 'w') as f:
    json.dump(config, f)
"

aws cloudfront update-distribution --id "$DIST_ID" --if-match "$ETAG" \
    --distribution-config file:///tmp/cf-config-updated.json \
    --profile "$PROFILE" --query 'Distribution.[Id,DomainName,Status]' --output table

echo ""
echo "Adding Route 53 alias records..."

aws route53 change-resource-record-sets --hosted-zone-id "$HOSTED_ZONE_ID" --profile "$PROFILE" --change-batch '{
  "Changes": [
    {
      "Action": "CREATE",
      "ResourceRecordSet": {
        "Name": "collectorstream.com",
        "Type": "A",
        "AliasTarget": {
          "HostedZoneId": "'"$CF_HOSTED_ZONE"'",
          "DNSName": "d1gbvo3xalwgl7.cloudfront.net",
          "EvaluateTargetHealth": false
        }
      }
    },
    {
      "Action": "CREATE",
      "ResourceRecordSet": {
        "Name": "www.collectorstream.com",
        "Type": "A",
        "AliasTarget": {
          "HostedZoneId": "'"$CF_HOSTED_ZONE"'",
          "DNSName": "d1gbvo3xalwgl7.cloudfront.net",
          "EvaluateTargetHealth": false
        }
      }
    }
  ]
}'

echo ""
echo "Done! collectorstream.com should be live once CloudFront finishes deploying."
echo "Test: https://collectorstream.com"
