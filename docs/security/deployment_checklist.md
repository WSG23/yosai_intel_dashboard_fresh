# Deployment Security Checklist

Follow this checklist before deploying to production to maintain a secure environment.

1. **Pre-deployment scans**
   - Run `trivy` to scan container images for vulnerabilities.
   - Run `bandit` to detect common security issues in Python code.
2. **Container registry scanning**
   - Ensure the container registry performs automated vulnerability scans on pushed images.
   - Block promotions of images with critical findings until they are remediated.
3. **Secrets rotation schedule**
   - Rotate API keys, credentials, and certificates on a regular cadence.
   - Track rotation dates and verify that old secrets are revoked.
4. **Monitoring and alerting hooks**
   - Connect deployments to monitoring systems to capture security events.
   - Configure alerting hooks for anomalous activity and failed scans.
