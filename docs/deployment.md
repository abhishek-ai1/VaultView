# 🚀 VaultView Deployment Guide

This guide covers various deployment options for VaultView, from simple development setups to production-ready configurations.

## 📋 Prerequisites

- **Python 3.8+**
- **Git**
- **Docker** (for containerized deployment)
- **Nginx** (for production reverse proxy)
- **SSL Certificate** (for HTTPS in production)

## 🏠 Development Deployment

### Local Development Setup

1. **Clone and setup**
   ```bash
   git clone https://github.com/yourusername/vaultview.git
   cd vaultview
   
   # Create virtual environment
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # or
   venv\Scripts\activate     # Windows
   
   # Install dependencies
   pip install -r requirements.txt
   ```

2. **Configure environment**
   ```bash
   # Copy example configuration
   cp instance/config.example.py instance/config.py
   
   # Edit configuration
   nano instance/config.py
   ```

3. **Initialize database**
   ```bash
   python -c "from vaultview.app import create_app; from vaultview.db import init_db; app = create_app(); init_db(app)"
   ```

4. **Run development server**
   ```bash
   python run.py
   ```

5. **Access application**
   - Open: `http://localhost:5000`
   - Register account and start using VaultView

## 🐳 Docker Deployment

### Single Container Deployment

1. **Build and run with Docker**
   ```bash
   # Build image
   docker build -t vaultview .
   
   # Run container
   docker run -d \
     --name vaultview \
     -p 5000:5000 \
     -e SECRET_KEY="your-secret-key-here" \
     -v vaultview_data:/app/instance \
     vaultview
   ```

2. **Using Docker Compose (Recommended)**
   ```bash
   # Create .env file
   cat > .env << EOF
   SECRET_KEY=your-super-secret-key-here
   FLASK_ENV=production
   DATABASE_URL=sqlite:///instance/vaultview.db
   EOF
   
   # Start services
   docker-compose up -d
   
   # View logs
   docker-compose logs -f vaultview
   ```

### Production Docker Setup

1. **Create production docker-compose.yml**
   ```yaml
   version: '3.8'
   
   services:
     vaultview:
       build: .
       container_name: vaultview-app
       restart: unless-stopped
       environment:
         - FLASK_ENV=production
         - SECRET_KEY=${SECRET_KEY}
         - DATABASE_URL=${DATABASE_URL}
       volumes:
         - vaultview_data:/app/instance
         - vaultview_logs:/app/logs
       networks:
         - vaultview-network
       depends_on:
         - redis
   
     redis:
       image: redis:7-alpine
       container_name: vaultview-redis
       restart: unless-stopped
       volumes:
         - redis_data:/data
       networks:
         - vaultview-network
   
     nginx:
       image: nginx:alpine
       container_name: vaultview-nginx
       restart: unless-stopped
       ports:
         - "80:80"
         - "443:443"
       volumes:
         - ./nginx.conf:/etc/nginx/nginx.conf:ro
         - ./ssl:/etc/nginx/ssl:ro
       depends_on:
         - vaultview
       networks:
         - vaultview-network
   
   volumes:
     vaultview_data:
     vaultview_logs:
     redis_data:
   
   networks:
     vaultview-network:
       driver: bridge
   ```

2. **Create Nginx configuration**
   ```nginx
   # nginx.conf
   events {
       worker_connections 1024;
   }
   
   http {
       upstream vaultview {
           server vaultview:5000;
       }
   
       server {
           listen 80;
           server_name your-domain.com;
           return 301 https://$server_name$request_uri;
       }
   
       server {
           listen 443 ssl http2;
           server_name your-domain.com;
   
           ssl_certificate /etc/nginx/ssl/cert.pem;
           ssl_certificate_key /etc/nginx/ssl/key.pem;
           ssl_protocols TLSv1.2 TLSv1.3;
           ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
           ssl_prefer_server_ciphers off;
   
           location / {
               proxy_pass http://vaultview;
               proxy_set_header Host $host;
               proxy_set_header X-Real-IP $remote_addr;
               proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
               proxy_set_header X-Forwarded-Proto $scheme;
           }
   
           location /static/ {
               proxy_pass http://vaultview/static/;
               expires 1y;
               add_header Cache-Control "public, immutable";
           }
       }
   }
   ```

3. **Deploy with SSL**
   ```bash
   # Create SSL directory
   mkdir -p ssl
   
   # Add your SSL certificates
   cp your-cert.pem ssl/cert.pem
   cp your-key.pem ssl/key.pem
   
   # Start services
   docker-compose up -d
   ```

## ☁️ Cloud Deployment

### AWS Deployment

#### Using AWS ECS

1. **Create ECS Task Definition**
   ```json
   {
     "family": "vaultview",
     "networkMode": "awsvpc",
     "requiresCompatibilities": ["FARGATE"],
     "cpu": "512",
     "memory": "1024",
     "executionRoleArn": "arn:aws:iam::123456789012:role/ecsTaskExecutionRole",
     "containerDefinitions": [
       {
         "name": "vaultview",
         "image": "your-account.dkr.ecr.region.amazonaws.com/vaultview:latest",
         "portMappings": [
           {
             "containerPort": 5000,
             "protocol": "tcp"
           }
         ],
         "environment": [
           {
             "name": "FLASK_ENV",
             "value": "production"
           },
           {
             "name": "SECRET_KEY",
             "value": "your-secret-key"
           }
         ],
         "logConfiguration": {
           "logDriver": "awslogs",
           "options": {
             "awslogs-group": "/ecs/vaultview",
             "awslogs-region": "us-east-1",
             "awslogs-stream-prefix": "ecs"
           }
         }
       }
     ]
   }
   ```

2. **Deploy with AWS CLI**
   ```bash
   # Build and push to ECR
   aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin your-account.dkr.ecr.us-east-1.amazonaws.com
   
   docker build -t vaultview .
   docker tag vaultview:latest your-account.dkr.ecr.us-east-1.amazonaws.com/vaultview:latest
   docker push your-account.dkr.ecr.us-east-1.amazonaws.com/vaultview:latest
   
   # Create ECS service
   aws ecs create-service \
     --cluster your-cluster \
     --service-name vaultview \
     --task-definition vaultview:1 \
     --desired-count 2 \
     --launch-type FARGATE \
     --network-configuration "awsvpcConfiguration={subnets=[subnet-12345],securityGroups=[sg-12345],assignPublicIp=ENABLED}"
   ```

#### Using AWS EC2

1. **Launch EC2 instance**
   ```bash
   # Launch Ubuntu 20.04 instance
   aws ec2 run-instances \
     --image-id ami-0c02fb55956c7d316 \
     --count 1 \
     --instance-type t3.medium \
     --key-name your-key-pair \
     --security-group-ids sg-12345
   ```

2. **Install dependencies**
   ```bash
   # Connect to instance
   ssh -i your-key.pem ubuntu@your-instance-ip
   
   # Update system
   sudo apt update && sudo apt upgrade -y
   
   # Install Python and dependencies
   sudo apt install -y python3 python3-pip python3-venv nginx
   
   # Clone repository
   git clone https://github.com/yourusername/vaultview.git
   cd vaultview
   
   # Setup application
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   pip install gunicorn
   ```

3. **Configure systemd service**
   ```bash
   # Create service file
   sudo tee /etc/systemd/system/vaultview.service << EOF
   [Unit]
   Description=VaultView Domain Security Monitor
   After=network.target
   
   [Service]
   User=ubuntu
   WorkingDirectory=/home/ubuntu/vaultview
   Environment="PATH=/home/ubuntu/vaultview/venv/bin"
   ExecStart=/home/ubuntu/vaultview/venv/bin/gunicorn --workers 4 --bind 127.0.0.1:5000 vaultview.app:create_app()
   Restart=always
   
   [Install]
   WantedBy=multi-user.target
   EOF
   
   # Start service
   sudo systemctl daemon-reload
   sudo systemctl enable vaultview
   sudo systemctl start vaultview
   ```

4. **Configure Nginx**
   ```bash
   # Create Nginx configuration
   sudo tee /etc/nginx/sites-available/vaultview << EOF
   server {
       listen 80;
       server_name your-domain.com;
   
       location / {
           proxy_pass http://127.0.0.1:5000;
           proxy_set_header Host \$host;
           proxy_set_header X-Real-IP \$remote_addr;
           proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto \$scheme;
       }
   }
   EOF
   
   # Enable site
   sudo ln -s /etc/nginx/sites-available/vaultview /etc/nginx/sites-enabled/
   sudo nginx -t
   sudo systemctl restart nginx
   ```

### Google Cloud Platform (GCP)

#### Using Google Cloud Run

1. **Build and deploy**
   ```bash
   # Set project
   gcloud config set project your-project-id
   
   # Build and push image
   gcloud builds submit --tag gcr.io/your-project-id/vaultview
   
   # Deploy to Cloud Run
   gcloud run deploy vaultview \
     --image gcr.io/your-project-id/vaultview \
     --platform managed \
     --region us-central1 \
     --allow-unauthenticated \
     --set-env-vars FLASK_ENV=production,SECRET_KEY=your-secret-key
   ```

#### Using Google Compute Engine

1. **Create VM instance**
   ```bash
   # Create instance
   gcloud compute instances create vaultview \
     --zone=us-central1-a \
     --machine-type=e2-medium \
     --image-family=ubuntu-2004-lts \
     --image-project=ubuntu-os-cloud \
     --tags=http-server,https-server
   
   # Allow HTTP/HTTPS traffic
   gcloud compute firewall-rules create allow-http \
     --allow tcp:80 \
     --target-tags=http-server \
     --description="Allow HTTP traffic"
   
   gcloud compute firewall-rules create allow-https \
     --allow tcp:443 \
     --target-tags=https-server \
     --description="Allow HTTPS traffic"
   ```

2. **Deploy application**
   ```bash
   # SSH to instance
   gcloud compute ssh vaultview --zone=us-central1-a
   
   # Follow EC2 deployment steps above
   ```

### Azure Deployment

#### Using Azure Container Instances

1. **Deploy container**
   ```bash
   # Build and push to Azure Container Registry
   az acr build --registry your-registry --image vaultview .
   
   # Deploy to Container Instances
   az container create \
     --resource-group your-rg \
     --name vaultview \
     --image your-registry.azurecr.io/vaultview:latest \
     --dns-name-label vaultview \
     --ports 5000 \
     --environment-variables FLASK_ENV=production SECRET_KEY=your-secret-key
   ```

## 🔧 Production Configuration

### Environment Variables

Create a `.env` file for production:

```bash
# Flask Configuration
FLASK_APP=vaultview.app
FLASK_ENV=production
SECRET_KEY=your-super-secret-key-here

# Database Configuration
DATABASE_URL=postgresql://user:password@localhost/vaultview

# Email Configuration
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password

# Security Configuration
WTF_CSRF_ENABLED=True
WTF_CSRF_TIME_LIMIT=3600
SSL_ALERT_DAYS=30

# Redis Configuration (for caching)
REDIS_URL=redis://localhost:6379/0

# Logging Configuration
LOG_LEVEL=INFO
LOG_FILE=/var/log/vaultview/app.log
```

### Database Setup

#### PostgreSQL (Recommended for Production)

1. **Install PostgreSQL**
   ```bash
   # Ubuntu/Debian
   sudo apt install postgresql postgresql-contrib
   
   # CentOS/RHEL
   sudo yum install postgresql postgresql-server
   ```

2. **Create database**
   ```bash
   sudo -u postgres psql
   
   CREATE DATABASE vaultview;
   CREATE USER vaultview_user WITH PASSWORD 'your_password';
   GRANT ALL PRIVILEGES ON DATABASE vaultview TO vaultview_user;
   \q
   ```

3. **Update configuration**
   ```python
   # instance/config.py
   SQLALCHEMY_DATABASE_URI = 'postgresql://vaultview_user:your_password@localhost/vaultview'
   ```

### SSL/TLS Configuration

#### Using Let's Encrypt

1. **Install Certbot**
   ```bash
   sudo apt install certbot python3-certbot-nginx
   ```

2. **Obtain certificate**
   ```bash
   sudo certbot --nginx -d your-domain.com
   ```

3. **Auto-renewal**
   ```bash
   sudo crontab -e
   # Add line:
   0 12 * * * /usr/bin/certbot renew --quiet
   ```

### Monitoring and Logging

#### Application Logging

1. **Configure logging**
   ```python
   # vaultview/app.py
   import logging
   from logging.handlers import RotatingFileHandler
   
   if not app.debug:
       if not os.path.exists('logs'):
           os.mkdir('logs')
       file_handler = RotatingFileHandler('logs/vaultview.log', maxBytes=10240, backupCount=10)
       file_handler.setFormatter(logging.Formatter(
           '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
       ))
       file_handler.setLevel(logging.INFO)
       app.logger.addHandler(file_handler)
       app.logger.setLevel(logging.INFO)
       app.logger.info('VaultView startup')
   ```

#### System Monitoring

1. **Setup monitoring with Prometheus**
   ```bash
   # Install Prometheus
   wget https://github.com/prometheus/prometheus/releases/download/v2.37.0/prometheus-2.37.0.linux-amd64.tar.gz
   tar xvf prometheus-*.tar.gz
   cd prometheus-*
   
   # Configure prometheus.yml
   cat > prometheus.yml << EOF
   global:
     scrape_interval: 15s
   
   scrape_configs:
     - job_name: 'vaultview'
       static_configs:
         - targets: ['localhost:5000']
   EOF
   
   # Start Prometheus
   ./prometheus --config.file=prometheus.yml
   ```

2. **Setup Grafana for visualization**
   ```bash
   # Install Grafana
   sudo apt install grafana
   sudo systemctl enable grafana-server
   sudo systemctl start grafana-server
   ```

## 🔒 Security Considerations

### Production Security Checklist

- [ ] **HTTPS Only**: Redirect all HTTP traffic to HTTPS
- [ ] **Strong Secret Key**: Use a cryptographically secure secret key
- [ ] **Database Security**: Use strong passwords and limit database access
- [ ] **Firewall Rules**: Configure firewall to allow only necessary ports
- [ ] **Regular Updates**: Keep system and dependencies updated
- [ ] **Backup Strategy**: Implement regular database backups
- [ ] **Monitoring**: Setup monitoring and alerting
- [ ] **Rate Limiting**: Implement rate limiting for API endpoints
- [ ] **Input Validation**: Validate all user inputs
- [ ] **CSRF Protection**: Ensure CSRF protection is enabled

### Security Headers

Add security headers in Nginx:

```nginx
# Add to server block
add_header X-Frame-Options "SAMEORIGIN" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header X-Content-Type-Options "nosniff" always;
add_header Referrer-Policy "no-referrer-when-downgrade" always;
add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;
```

## 📊 Performance Optimization

### Gunicorn Configuration

```bash
# gunicorn.conf.py
bind = "0.0.0.0:5000"
workers = 4
worker_class = "gevent"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 50
timeout = 120
keepalive = 2
preload_app = True
```

### Caching Strategy

1. **Redis Caching**
   ```python
   # vaultview/cache.py
   import redis
   import json
   
   redis_client = redis.Redis(host='localhost', port=6379, db=0)
   
   def cache_result(key, data, expire=3600):
       redis_client.setex(key, expire, json.dumps(data))
   
   def get_cached_result(key):
       data = redis_client.get(key)
       return json.loads(data) if data else None
   ```

2. **Application Caching**
   ```python
   # Use Flask-Caching
   from flask_caching import Cache
   
   cache = Cache(config={'CACHE_TYPE': 'redis', 'CACHE_REDIS_URL': 'redis://localhost:6379/0'})
   cache.init_app(app)
   ```

## 🔄 Backup and Recovery

### Database Backup

```bash
# PostgreSQL backup script
#!/bin/bash
BACKUP_DIR="/backups/vaultview"
DATE=$(date +%Y%m%d_%H%M%S)
DB_NAME="vaultview"

mkdir -p $BACKUP_DIR
pg_dump $DB_NAME > $BACKUP_DIR/vaultview_$DATE.sql

# Keep only last 7 days of backups
find $BACKUP_DIR -name "*.sql" -mtime +7 -delete
```

### Application Backup

```bash
# Backup application data
#!/bin/bash
BACKUP_DIR="/backups/vaultview"
DATE=$(date +%Y%m%d_%H%M%S)

tar -czf $BACKUP_DIR/vaultview_app_$DATE.tar.gz \
  /path/to/vaultview/instance \
  /path/to/vaultview/logs
```

## 🆘 Troubleshooting

### Common Issues

1. **Database Connection Issues**
   ```bash
   # Check database connectivity
   python -c "from vaultview.app import create_app; app = create_app(); print('Database OK')"
   ```

2. **Permission Issues**
   ```bash
   # Fix file permissions
   sudo chown -R www-data:www-data /path/to/vaultview
   sudo chmod -R 755 /path/to/vaultview
   ```

3. **Port Conflicts**
   ```bash
   # Check port usage
   sudo netstat -tlnp | grep :5000
   sudo lsof -i :5000
   ```

### Log Analysis

```bash
# View application logs
tail -f /var/log/vaultview/app.log

# View system logs
sudo journalctl -u vaultview -f

# View Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

## 📞 Support

For deployment support:
- **Documentation**: [docs/](docs/)
- **Issues**: [GitHub Issues](https://github.com/yourusername/vaultview/issues)
- **Email**: deployment-support@vaultview.com 