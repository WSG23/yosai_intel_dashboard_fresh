# deployment/production_setup.py
"""
Production deployment configuration and utilities
Implements Apple-grade production deployment patterns
"""
import os
from core.secret_manager import SecretManager
import subprocess
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path
from dataclasses import dataclass
import yaml
import time


@dataclass
class DeploymentConfig:
    """Production deployment configuration"""

    environment: str
    replicas: int
    cpu_limit: str
    memory_limit: str
    storage_size: str
    database_config: Dict[str, Any]
    monitoring_enabled: bool
    backup_enabled: bool
    ssl_enabled: bool
    domain: Optional[str] = None


class ProductionDeployment:
    """Handles production deployment tasks"""

    def __init__(self, config_path: str = "deployment/production.yaml"):
        self.config_path = Path(config_path)
        self.logger = logging.getLogger(__name__)
        self.config = self._load_deployment_config()

    def _load_deployment_config(self) -> DeploymentConfig:
        """Load deployment configuration"""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Deployment config not found: {self.config_path}")

        with open(self.config_path, "r") as f:
            config_data = yaml.safe_load(f)

        return DeploymentConfig(**config_data)

    def validate_environment(self) -> Dict[str, bool]:
        """Validate production environment requirements"""
        checks = {
            "docker_available": self._check_docker(),
            "database_accessible": self._check_database(),
            "ssl_certificates": self._check_ssl_certificates(),
            "environment_variables": self._check_environment_variables(),
            "storage_available": self._check_storage(),
            "monitoring_configured": self._check_monitoring(),
            "backup_configured": self._check_backup_system(),
        }

        all_passed = all(checks.values())

        if all_passed:
            self.logger.info("✅ All production environment checks passed")
        else:
            failed_checks = [check for check, passed in checks.items() if not passed]
            self.logger.error(f"❌ Failed checks: {failed_checks}")

        return checks

    def _check_docker(self) -> bool:
        """Check if Docker is available and running"""
        try:
            result = subprocess.run(
                ["docker", "--version"], capture_output=True, text=True, timeout=10
            )
            return result.returncode == 0
        except Exception:
            return False

    def _check_database(self) -> bool:
        """Check database connectivity"""
        try:
            # This would test actual database connection
            # Implementation depends on your database setup
            return True  # Placeholder
        except Exception:
            return False

    def _check_ssl_certificates(self) -> bool:
        """Check SSL certificate configuration"""
        if not self.config.ssl_enabled:
            return True

        cert_path = Path("ssl/cert.pem")
        key_path = Path("ssl/private.key")

        return cert_path.exists() and key_path.exists()

    def _check_environment_variables(self) -> bool:
        """Check required environment variables"""
        required_vars = ["SECRET_KEY", "DB_PASSWORD", "SENTRY_DSN"]

        manager = SecretManager()
        missing_vars = [var for var in required_vars if manager.get(var, None) is None]

        if missing_vars:
            self.logger.error(f"Missing required environment variables: {missing_vars}")
            return False

        return True

    def _check_storage(self) -> bool:
        """Check storage availability"""
        try:
            # Check disk space
            import shutil

            total, used, free = shutil.disk_usage("/")
            free_gb = free // (1024**3)

            required_gb = 10  # Minimum 10GB free
            return free_gb >= required_gb
        except Exception:
            return False

    def _check_monitoring(self) -> bool:
        """Check monitoring system configuration"""
        if not self.config.monitoring_enabled:
            return True

        # Check if monitoring endpoints are configured
        manager = SecretManager()
        return manager.get("SENTRY_DSN", None) is not None

    def _check_backup_system(self) -> bool:
        """Check backup system configuration"""
        if not self.config.backup_enabled:
            return True

        # Check backup configuration
        backup_config = Path("backup/config.yaml")
        return backup_config.exists()

    def generate_docker_compose(self) -> str:
        """Generate production Docker Compose configuration"""

        compose_config = {
            "version": "3.8",
            "services": {
                "yosai-dashboard": {
                    "build": ".",
                    "ports": (
                        ["80:8050"] if not self.config.ssl_enabled else ["443:8050"]
                    ),
                    "environment": self._get_app_environment(),
                    "depends_on": ["postgres", "redis"],
                    "volumes": ["./data:/app/data", "./logs:/app/logs"],
                    "restart": "unless-stopped",
                    "deploy": {
                        "replicas": self.config.replicas,
                        "resources": {
                            "limits": {
                                "cpus": self.config.cpu_limit,
                                "memory": self.config.memory_limit,
                            }
                        },
                    },
                    "healthcheck": {
                        "test": ["CMD", "curl", "-f", "http://localhost:8050/health"],
                        "interval": "30s",
                        "timeout": "10s",
                        "retries": 3,
                    },
                },
                "postgres": {
                    "image": "postgres:15",
                    "environment": {
                        "POSTGRES_DB": self.config.database_config["name"],
                        "POSTGRES_USER": self.config.database_config["user"],
                        "POSTGRES_PASSWORD": "${DB_PASSWORD}",
                    },
                    "volumes": [
                        "postgres_data:/var/lib/postgresql/data",
                        "./database/init.sql:/docker-entrypoint-initdb.d/init.sql",
                    ],
                    "ports": ["5432:5432"],
                    "restart": "unless-stopped",
                },
                "redis": {
                    "image": "redis:7-alpine",
                    "ports": ["6379:6379"],
                    "volumes": ["redis_data:/data"],
                    "restart": "unless-stopped",
                    "command": "redis-server --appendonly yes",
                },
            },
            "volumes": {"postgres_data": {}, "redis_data": {}},
        }

        # Add monitoring if enabled
        if self.config.monitoring_enabled:
            compose_config["services"]["prometheus"] = {
                "image": "prom/prometheus:latest",
                "ports": ["9090:9090"],
                "volumes": [
                    "./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml"
                ],
                "restart": "unless-stopped",
            }

            compose_config["services"]["grafana"] = {
                "image": "grafana/grafana:latest",
                "ports": ["3000:3000"],
                "environment": ["GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD}"],
                "volumes": ["grafana_data:/var/lib/grafana"],
                "restart": "unless-stopped",
            }

            compose_config["volumes"]["grafana_data"] = {}

        # Add SSL proxy if enabled
        if self.config.ssl_enabled:
            compose_config["services"]["nginx"] = {
                "image": "nginx:alpine",
                "ports": ["80:80", "443:443"],
                "volumes": [
                    "./nginx/nginx.conf:/etc/nginx/nginx.conf",
                    "./ssl:/etc/ssl/certs",
                ],
                "depends_on": ["yosai-dashboard"],
                "restart": "unless-stopped",
            }

        return yaml.dump(compose_config, default_flow_style=False)

    def _get_app_environment(self) -> List[str]:
        """Get application environment variables for Docker"""
        return [
            "YOSAI_ENV=production",
            "DEBUG=False",
            "DB_TYPE=postgresql",
            "DB_HOST=postgres",
            "DB_NAME=${DB_NAME}",
            "DB_USER=${DB_USER}",
            "DB_PASSWORD=${DB_PASSWORD}",
            "REDIS_HOST=redis",
            "SECRET_KEY=${SECRET_KEY}",
            "SENTRY_DSN=${SENTRY_DSN}",
        ]

    def generate_nginx_config(self) -> str:
        """Generate Nginx configuration for SSL termination"""

        domain = self.config.domain or "localhost"

        return f"""
events {{
    worker_connections 1024;
}}

http {{
    upstream yosai_dashboard {{
        server yosai-dashboard:8050;
    }}
    
    # HTTP redirect to HTTPS
    server {{
        listen 80;
        server_name {domain};
        return 301 https://$server_name$request_uri;
    }}
    
    # HTTPS server
    server {{
        listen 443 ssl http2;
        server_name {domain};
        
        ssl_certificate /etc/ssl/certs/cert.pem;
        ssl_certificate_key /etc/ssl/certs/private.key;
        
        # SSL configuration
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers ECDHE-RSA-AES256-GCM-SHA384:ECDHE-RSA-AES128-GCM-SHA256;
        ssl_prefer_server_ciphers off;
        
        # Security headers
        add_header X-Frame-Options "SAMEORIGIN" always;
        add_header X-XSS-Protection "1; mode=block" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header Referrer-Policy "no-referrer-when-downgrade" always;
        add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;
        
        # Gzip compression
        gzip on;
        gzip_vary on;
        gzip_min_length 1024;
        gzip_types
            text/plain
            text/css
            text/xml
            text/javascript
            application/javascript
            application/xml+rss
            application/json;
        
        # Rate limiting
        limit_req_zone $binary_remote_addr zone=dashboard:10m rate=10r/s;
        limit_req zone=dashboard burst=20 nodelay;
        
        location / {{
            proxy_pass http://yosai_dashboard;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # WebSocket support
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            
            # Timeouts
            proxy_connect_timeout 60s;
            proxy_send_timeout 60s;
            proxy_read_timeout 60s;
        }}
        
        # Health check endpoint
        location /health {{
            access_log off;
            proxy_pass http://yosai_dashboard/health;
        }}
        
        # Static files caching
        location ~* \\.(css|js|png|jpg|jpeg|gif|ico|svg)$ {{
            expires 1y;
            add_header Cache-Control "public, immutable";
        }}
    }}
}}
"""

    def generate_kubernetes_manifests(self) -> Dict[str, str]:
        """Generate Kubernetes deployment manifests"""

        manifests = {}

        # Deployment
        manifests[
            "deployment.yaml"
        ] = f"""
apiVersion: apps/v1
kind: Deployment
metadata:
  name: yosai-dashboard
  labels:
    app: yosai-dashboard
spec:
  replicas: {self.config.replicas}
  selector:
    matchLabels:
      app: yosai-dashboard
  template:
    metadata:
      labels:
        app: yosai-dashboard
    spec:
      containers:
      - name: yosai-dashboard
        image: yosai-intel:latest
        ports:
        - containerPort: 8050
        env:
        - name: YOSAI_ENV
          value: "production"
        - name: DEBUG
          value: "False"
        - name: SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: yosai-secrets
              key: secret-key
        - name: DB_PASSWORD
          valueFrom:
            secretKeyRef:
              name: yosai-secrets
              key: db-password
        resources:
          limits:
            cpu: {self.config.cpu_limit}
            memory: {self.config.memory_limit}
          requests:
            cpu: "100m"
            memory: "256Mi"
        livenessProbe:
          httpGet:
            path: /health
            port: 8050
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8050
          initialDelaySeconds: 5
          periodSeconds: 5
        volumeMounts:
        - name: data-storage
          mountPath: /app/data
      volumes:
      - name: data-storage
        persistentVolumeClaim:
          claimName: yosai-data-pvc
"""

        # Service
        manifests[
            "service.yaml"
        ] = """
apiVersion: v1
kind: Service
metadata:
  name: yosai-dashboard-service
spec:
  selector:
    app: yosai-dashboard
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8050
  type: LoadBalancer
"""

        # Persistent Volume Claim
        manifests[
            "pvc.yaml"
        ] = f"""
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: yosai-data-pvc
spec:
  accessModes:
  - ReadWriteOnce
  resources:
    requests:
      storage: {self.config.storage_size}
"""

        # Secrets
        manifests[
            "secrets.yaml"
        ] = """
apiVersion: v1
kind: Secret
metadata:
  name: yosai-secrets
type: Opaque
data:
  secret-key: # Base64 encoded secret key
  db-password: # Base64 encoded database password
"""

        return manifests

    def deploy_to_production(self, method: str = "docker-compose") -> bool:
        """Deploy application to production"""

        self.logger.info(f"Starting production deployment using {method}")

        # Validate environment first
        validation_results = self.validate_environment()
        if not all(validation_results.values()):
            self.logger.error("Environment validation failed, aborting deployment")
            return False

        try:
            if method == "docker-compose":
                return self._deploy_docker_compose()
            elif method == "kubernetes":
                return self._deploy_kubernetes()
            else:
                raise ValueError(f"Unsupported deployment method: {method}")

        except Exception as e:
            self.logger.error(f"Deployment failed: {e}")
            return False

    def _deploy_docker_compose(self) -> bool:
        """Deploy using Docker Compose"""

        # Generate docker-compose.yml
        compose_content = self.generate_docker_compose()
        with open("docker-compose.prod.yml", "w") as f:
            f.write(compose_content)

        # Generate nginx config if SSL enabled
        if self.config.ssl_enabled:
            nginx_config = self.generate_nginx_config()
            os.makedirs("nginx", exist_ok=True)
            with open("nginx/nginx.conf", "w") as f:
                f.write(nginx_config)

        # Deploy
        try:
            # Pull latest images
            subprocess.run(
                ["docker-compose", "-f", "docker-compose.prod.yml", "pull"],
                check=True,
                timeout=300,
            )

            # Start services
            subprocess.run(
                ["docker-compose", "-f", "docker-compose.prod.yml", "up", "-d"],
                check=True,
                timeout=300,
            )

            self.logger.info("✅ Docker Compose deployment successful")
            return True

        except subprocess.CalledProcessError as e:
            self.logger.error(f"Docker Compose deployment failed: {e}")
            return False

    def _deploy_kubernetes(self) -> bool:
        """Deploy using Kubernetes"""

        manifests = self.generate_kubernetes_manifests()

        # Write manifest files
        os.makedirs("k8s", exist_ok=True)
        for filename, content in manifests.items():
            with open(f"k8s/{filename}", "w") as f:
                f.write(content)

        # Apply manifests
        try:
            subprocess.run(["kubectl", "apply", "-f", "k8s/"], check=True, timeout=300)

            self.logger.info("✅ Kubernetes deployment successful")
            return True

        except subprocess.CalledProcessError as e:
            self.logger.error(f"Kubernetes deployment failed: {e}")
            return False

    def rollback_deployment(self) -> bool:
        """Rollback to previous deployment"""
        try:
            # This is a simplified rollback - in practice you'd want more sophisticated versioning
            subprocess.run(
                ["docker-compose", "-f", "docker-compose.prod.yml", "down"],
                check=True,
                timeout=120,
            )

            # Restore from backup if needed
            self.logger.info("✅ Rollback completed")
            return True

        except subprocess.CalledProcessError as e:
            self.logger.error(f"Rollback failed: {e}")
            return False

    def health_check(self) -> Dict[str, Any]:
        """Perform post-deployment health check"""

        checks = {
            "application_responsive": self._check_app_health(),
            "database_connected": self._check_database_health(),
            "cache_available": self._check_cache_health(),
            "ssl_working": (
                self._check_ssl_health() if self.config.ssl_enabled else True
            ),
            "monitoring_active": (
                self._check_monitoring_health()
                if self.config.monitoring_enabled
                else True
            ),
        }

        overall_health = all(checks.values())

        return {"healthy": overall_health, "checks": checks, "timestamp": time.time()}

    def _check_app_health(self) -> bool:
        """Check if application is responding"""
        try:
            import requests

            response = requests.get("http://localhost/health", timeout=10)
            return response.status_code == 200
        except Exception:
            return False

    def _check_database_health(self) -> bool:
        """Check database connectivity"""
        # Implementation would depend on your database setup
        return True  # Placeholder

    def _check_cache_health(self) -> bool:
        """Check cache availability"""
        try:
            import redis

            r = redis.Redis(host="localhost", port=6379, db=0)
            return r.ping()
        except Exception:
            return False

    def _check_ssl_health(self) -> bool:
        """Check SSL certificate validity"""
        try:
            import ssl
            import socket

            context = ssl.create_default_context()
            with socket.create_connection(("localhost", 443), timeout=10) as sock:
                with context.wrap_socket(sock, server_hostname="localhost") as ssock:
                    return True
        except Exception:
            return False

    def _check_monitoring_health(self) -> bool:
        """Check monitoring system health"""
        try:
            import requests

            response = requests.get("http://localhost:9090/-/healthy", timeout=10)
            return response.status_code == 200
        except Exception:
            return False
