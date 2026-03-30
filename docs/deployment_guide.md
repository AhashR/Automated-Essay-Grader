# Deployment Guide - Automated Essay Grader

This guide provides instructions for deploying the Automated Essay Grader in various environments.

## Table of Contents

1. [Local Development](#local-development)
2. [Production Deployment](#production-deployment)
3. [Cloud Deployment](#cloud-deployment)
4. [Docker Deployment](#docker-deployment)
5. [Environment Configuration](#environment-configuration)
6. [Security Considerations](#security-considerations)
7. [Monitoring and Maintenance](#monitoring-and-maintenance)

## Local Development

### Prerequisites

- Python 3.10 or higher
- Git
- Virtual environment tool (venv, conda, etc.)

### Setup Steps

1. **Clone the Repository**
   ```bash
   git clone https://github.com/Hasif50/Automated-Essay-Grader.git
   cd Automated-Essay-Grader
   ```

2. **Create Virtual Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Environment**
   ```bash
   cp .env.sample .env
   # Edit .env with your API keys
   ```

5. **Run the Application**
   ```bash
   python app.py
   ```

6. **Access the Application**
   - Open browser to `http://localhost:5000`

## Production Deployment

### Server Requirements

- **CPU**: 2+ cores recommended
- **RAM**: 4GB minimum, 8GB recommended
- **Storage**: 10GB minimum
- **OS**: Linux (Ubuntu 20.04+ recommended)
- **Python**: 3.10+

### Production Setup

1. **System Updates**
   ```bash
   sudo apt update && sudo apt upgrade -y
   sudo apt install python3.10 python3.10-venv python3-pip nginx -y
   ```

2. **Application Setup**
   ```bash
   cd /opt
   sudo git clone https://github.com/Hasif50/Automated-Essay-Grader.git
   sudo chown -R $USER:$USER Automated-Essay-Grader
   cd Automated-Essay-Grader
   ```

3. **Virtual Environment**
   ```bash
   python3.10 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

4. **Environment Configuration**
   ```bash
   cp .env.sample .env
   # Configure production settings
   nano .env
   ```

5. **Service Configuration**
   Create systemd service file:
   ```bash
   sudo nano /etc/systemd/system/essay-grader.service
   ```

   Service file content:
   ```ini
   [Unit]
   Description=Automated Essay Grader
   After=network.target

   [Service]
   Type=simple
   User=www-data
   WorkingDirectory=/opt/Automated-Essay-Grader
   Environment=PATH=/opt/Automated-Essay-Grader/venv/bin
   ExecStart=/opt/Automated-Essay-Grader/venv/bin/python app.py
   Restart=always

   [Install]
   WantedBy=multi-user.target
   ```

6. **Start Service**
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable essay-grader
   sudo systemctl start essay-grader
   ```

### Nginx Configuration

1. **Create Nginx Config**
   ```bash
   sudo nano /etc/nginx/sites-available/essay-grader
   ```

2. **Configuration Content**
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;

       location / {
            proxy_pass http://localhost:5000;
           proxy_http_version 1.1;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
   }
   ```

3. **Enable Site**
   ```bash
   sudo ln -s /etc/nginx/sites-available/essay-grader /etc/nginx/sites-enabled/
   sudo nginx -t
   sudo systemctl restart nginx
   ```

## Cloud Deployment

### Flask-Compatible PaaS (Render/Railway/Heroku)

1. **Prepare Repository**
   - Ensure all files are committed to GitHub
   - Verify `requirements.txt` is complete
   - Configure environment variables in your platform dashboard

2. **Start Command**
   - Use: `python app.py`

3. **Environment Variables**
   Add these variables in your deployment platform:
   - `OPENAI_API_KEY`
   - `AZURE_API_KEY`
   - `AZURE_ENDPOINT`
   - `PORT` (provided by platform on most PaaS providers)

### Heroku Deployment

1. **Prepare Files**
   Create `Procfile`:
   ```
   web: python app.py
   ```

   Create `runtime.txt`:
   ```
   python-3.10.8
   ```

2. **Deploy Commands**
   ```bash
   heroku create your-app-name
   heroku config:set OPENAI_API_KEY=your_key_here
   git push heroku main
   ```

### AWS EC2 Deployment

1. **Launch EC2 Instance**
   - Choose Ubuntu 20.04 LTS
   - t3.medium or larger recommended
   - Configure security groups (ports 22, 80, 443)

2. **Setup Application**
   ```bash
   ssh -i your-key.pem ubuntu@your-ec2-ip
   # Follow production setup steps above
   ```

3. **Load Balancer (Optional)**
   - Configure Application Load Balancer
   - Set up health checks
   - Configure SSL certificate

## Docker Deployment

### Dockerfile

Create `Dockerfile`:
```dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

HEALTHCHECK CMD curl --fail http://localhost:5000/health

ENTRYPOINT ["python", "app.py"]
```

### Docker Compose

Create `docker-compose.yml`:
```yaml
version: '3.8'

services:
  essay-grader:
    build: .
    ports:
         - "5000:5000"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - AZURE_API_KEY=${AZURE_API_KEY}
      - AZURE_ENDPOINT=${AZURE_ENDPOINT}
    volumes:
      - ./data/outputs:/app/data/outputs
      - ./logs:/app/logs
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - essay-grader
    restart: unless-stopped
```

### Build and Run

```bash
docker-compose up -d
```

## Environment Configuration

### Required Variables

```bash
# AI Model Configuration
OPENAI_API_KEY=your_openai_key
OPENAI_MODEL=gpt-4
OPENAI_TEMPERATURE=0.3
OPENAI_MAX_TOKENS=2000

# Azure Configuration (if using Azure)
AZURE_API_KEY=your_azure_key
AZURE_ENDPOINT=your_azure_endpoint
AZURE_API_VERSION=2023-05-15

# Application Settings
APP_TITLE="Automated Essay Grader"
MAX_ESSAY_LENGTH=10000
DEFAULT_RUBRIC=learning_story

# Security
SECRET_KEY=your_secret_key_here
ALLOWED_HOSTS=localhost,your-domain.com
```

### Optional Variables

```bash
# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/app.log

# Features
ENABLE_PLAGIARISM_CHECK=true
ENABLE_GRAMMAR_CHECK=true
ENABLE_STYLE_ANALYSIS=true

# File Upload
MAX_FILE_SIZE=10MB
ALLOWED_EXTENSIONS=pdf,docx,txt
```

## Security Considerations

### API Key Management

1. **Never commit API keys to version control**
2. **Use environment variables or secret management**
3. **Rotate keys regularly**
4. **Monitor API usage and costs**

### Application Security

1. **Input Validation**
   - Validate file types and sizes
   - Sanitize text input
   - Implement rate limiting

2. **Network Security**
   - Use HTTPS in production
   - Configure firewall rules
   - Implement reverse proxy

3. **Data Protection**
   - Don't store essay content permanently
   - Implement data retention policies
   - Ensure GDPR compliance if applicable

### Production Hardening

```bash
# Firewall configuration
sudo ufw enable
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'

# SSL Certificate (Let's Encrypt)
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

## Monitoring and Maintenance

### Health Checks

1. **Application Health**
   ```bash
   curl http://localhost:5000/health
   ```

2. **Service Status**
   ```bash
   sudo systemctl status essay-grader
   sudo systemctl status nginx
   ```

### Logging

1. **Application Logs**
   ```bash
   tail -f logs/app.log
   ```

2. **System Logs**
   ```bash
   sudo journalctl -u essay-grader -f
   ```

### Backup Strategy

1. **Configuration Backup**
   ```bash
   # Backup environment and config files
   tar -czf backup-$(date +%Y%m%d).tar.gz .env config/ data/rubrics/
   ```

2. **Database Backup** (if applicable)
   ```bash
   # Backup any persistent data
   ```

### Updates and Maintenance

1. **Application Updates**
   ```bash
   cd /opt/Automated-Essay-Grader
   git pull origin main
   source venv/bin/activate
   pip install -r requirements.txt
   sudo systemctl restart essay-grader
   ```

2. **System Updates**
   ```bash
   sudo apt update && sudo apt upgrade -y
   sudo reboot  # if kernel updates
   ```

### Performance Monitoring

1. **Resource Usage**
   ```bash
   htop
   df -h
   free -h
   ```

2. **Application Metrics**
   - Monitor response times
   - Track API usage and costs
   - Monitor error rates

## Troubleshooting

### Common Issues

1. **Port Already in Use**
   ```bash
   sudo lsof -i :5000
   sudo kill -9 <PID>
   ```

2. **Permission Issues**
   ```bash
   sudo chown -R www-data:www-data /opt/Automated-Essay-Grader
   ```

3. **SSL Certificate Issues**
   ```bash
   sudo certbot renew --dry-run
   ```

### Log Analysis

```bash
# Check application errors
grep -i error logs/app.log

# Check system errors
sudo journalctl -u essay-grader --since "1 hour ago"
```

---

## Support

For deployment support or issues:

1. Check the troubleshooting section
2. Review application logs
3. Consult the user guide
4. Contact the development team

**Built from Hasif's Workspace**  
**Author**: Hasif50  
**Version**: 1.0.0