#!/usr/bin/env bash
set -euo pipefail
# Simple security hardening script
# Configures VPC firewall rules, generates TLS certificates, and prepares basic SSO configuration.


# Ensure required tools are available
command -v openssl >/dev/null 2>&1 || { echo "openssl is required" >&2; exit 1; }
if ! command -v aws >/dev/null 2>&1; then
    echo "aws CLI not found. VPC configuration will be skipped." >&2
    SKIP_AWS=1
else
    SKIP_AWS=0
fi

SECURITY_GROUP_ID="${SECURITY_GROUP_ID:-}"      # AWS security group ID for VPC rules
CERT_DIR="${CERT_DIR:-/etc/ssl/local}"          # Location to store generated certificates
DOMAIN="${DOMAIN:-localhost}"                   # Domain for TLS certificate
SSO_PROVIDER_URL="${SSO_PROVIDER_URL:-}"        # SSO provider URL
SSO_CLIENT_ID="${SSO_CLIENT_ID:-}"              # SSO client identifier

# 1. Configure VPC rules using AWS security groups
if [ "$SKIP_AWS" -eq 0 ] && [ -n "$SECURITY_GROUP_ID" ]; then
    echo "Configuring VPC rules for security group $SECURITY_GROUP_ID"
    aws ec2 authorize-security-group-ingress --group-id "$SECURITY_GROUP_ID" \
        --protocol tcp --port 443 --cidr 0.0.0.0/0 || true
    aws ec2 authorize-security-group-ingress --group-id "$SECURITY_GROUP_ID" \
        --protocol tcp --port 80 --cidr 0.0.0.0/0 || true
fi

# 2. Generate self-signed TLS certificates if none exist
mkdir -p "$CERT_DIR"
CRT_FILE="$CERT_DIR/${DOMAIN}.crt"
KEY_FILE="$CERT_DIR/${DOMAIN}.key"

if [ ! -f "$CRT_FILE" ] || [ ! -f "$KEY_FILE" ]; then
    echo "Generating TLS certificate for $DOMAIN"
    openssl req -newkey rsa:2048 -nodes -keyout "$KEY_FILE" -x509 -days 365 \
        -out "$CRT_FILE" -subj "/CN=$DOMAIN"
fi

# 3. Configure basic SSO settings
if [ -n "$SSO_PROVIDER_URL" ] && [ -n "$SSO_CLIENT_ID" ]; then
    echo "Writing SSO configuration"
    cat > sso_config.env <<EOF_CONF
SSO_PROVIDER_URL=$SSO_PROVIDER_URL
SSO_CLIENT_ID=$SSO_CLIENT_ID
EOF_CONF
fi

echo "Security hardening complete."

