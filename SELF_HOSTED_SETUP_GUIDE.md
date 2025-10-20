# StoryKeep Self-Hosted Server Setup Guide

Complete guide to deploy StoryKeep on your own server.

---

## 📋 Table of Contents
1. [Server Requirements](#server-requirements)
2. [Software Dependencies](#software-dependencies)
3. [Installation Steps](#installation-steps)
4. [Configuration](#configuration)
5. [Database Setup](#database-setup)
6. [File Storage Setup](#file-storage-setup)
7. [Production Deployment](#production-deployment)
8. [Security Hardening](#security-hardening)
9. [Maintenance](#maintenance)

---

## 🖥️ Server Requirements

### Minimum Specifications
- **OS**: Ubuntu 22.04 LTS or later (recommended), CentOS 8+, Debian 11+
- **CPU**: 2 cores
- **RAM**: 4 GB
- **Storage**: 50 GB SSD (+ additional for photo storage)
- **Network**: Public IP address with ports 80/443 open

### Recommended Specifications
- **OS**: Ubuntu 22.04 LTS
- **CPU**: 4 cores
- **RAM**: 8 GB
- **Storage**: 100 GB SSD + separate volume for photos
- **Network**: Public IP with domain name

---

## 📦 Software Dependencies

### Core Software
```bash
# System
- Ubuntu 22.04 LTS
- Python 3.11 or 3.12
- PostgreSQL 14+
- Nginx
- Supervisor (for process management)

# Optional but Recommended
- Certbot (for SSL/HTTPS)
- UFW (firewall)
- Fail2ban (security)
```

---

## 🚀 Installation Steps

### Step 1: Update System
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y build-essential python3-dev python3-pip python3-venv \
  postgresql postgresql-contrib nginx supervisor git curl
```

### Step 2: Install Python 3.11/3.12
```bash
# If Ubuntu 22.04 doesn't have Python 3.11+, add deadsnakes PPA
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt update
sudo apt install -y python3.11 python3.11-venv python3.11-dev

# Verify installation
python3.11 --version
```

### Step 3: Create Application User
```bash
# Create dedicated user for security
sudo adduser --system --group --home /opt/storykeep storykeep
sudo su - storykeep
```

### Step 4: Clone Repository
```bash
# As storykeep user
cd /opt/storykeep
git clone https://github.com/YOUR_USERNAME/YOUR_REPO.git app
cd app
```

### Step 5: Create Virtual Environment
```bash
# As storykeep user in /opt/storykeep/app
python3.11 -m venv venv
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip setuptools wheel
```

### Step 6: Install Python Dependencies
```bash
# As storykeep user with venv activated
pip install -r requirements.txt

# Verify gunicorn installation
gunicorn --version
```

---

## 🗄️ Database Setup

### Step 1: Create PostgreSQL Database
```bash
# Switch to postgres user
sudo -u postgres psql

# In PostgreSQL prompt:
CREATE USER storykeep_user WITH PASSWORD 'your_secure_password_here';
CREATE DATABASE storykeep_db OWNER storykeep_user;
GRANT ALL PRIVILEGES ON DATABASE storykeep_db TO storykeep_user;
\q
```

### Step 2: Configure PostgreSQL Access
```bash
# Edit pg_hba.conf
sudo nano /etc/postgresql/14/main/pg_hba.conf

# Add this line (for local access):
local   storykeep_db    storykeep_user                      md5

# Restart PostgreSQL
sudo systemctl restart postgresql
```

### Step 3: Test Database Connection
```bash
# As storykeep user
psql -U storykeep_user -d storykeep_db -h localhost
# Enter password when prompted
\q
```

---

## 📁 File Storage Setup

### Create Upload Directory
```bash
# As root
sudo mkdir -p /data/storykeep/uploads
sudo chown -R storykeep:storykeep /data/storykeep
sudo chmod 755 /data/storykeep
sudo chmod 755 /data/storykeep/uploads
```

### Optional: Mount External Storage
```bash
# If using separate disk/volume for photos
sudo mkfs.ext4 /dev/sdb  # Replace with your device
sudo mount /dev/sdb /data/storykeep
sudo chown -R storykeep:storykeep /data/storykeep

# Add to /etc/fstab for auto-mount on boot
echo "/dev/sdb /data/storykeep ext4 defaults 0 2" | sudo tee -a /etc/fstab
```

---

## ⚙️ Configuration

### Step 1: Create Environment File
```bash
# As storykeep user in /opt/storykeep/app
nano .env
```

```bash
# .env file contents:

# Flask Configuration
FLASK_CONFIG=production
SECRET_KEY=your_random_secret_key_generate_with_openssl_rand_base64_32

# Database
DATABASE_URL=postgresql://storykeep_user:your_secure_password_here@localhost/storykeep_db

# File Storage
UPLOAD_FOLDER=/data/storykeep/uploads

# Email Configuration (SendGrid)
MAIL_SERVER=smtp.sendgrid.net
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=apikey
MAIL_PASSWORD=your_sendgrid_api_key

# Stripe Payment (if using subscriptions)
STRIPE_PUBLIC_KEY=pk_live_xxxxx
STRIPE_SECRET_KEY=sk_live_xxxxx
STRIPE_WEBHOOK_SECRET=whsec_xxxxx

# OpenAI (for AI features)
OPENAI_API_KEY=sk-xxxxx

# Google Gemini (alternative AI)
GOOGLE_API_KEY=xxxxx

# Application Settings
HTTPS=true
LOG_TO_STDOUT=1
```

### Step 2: Generate Secret Key
```bash
# Generate secure SECRET_KEY
openssl rand -base64 32
# Copy output to .env file
```

### Step 3: Initialize Database
```bash
# As storykeep user with venv activated
cd /opt/storykeep/app
source venv/bin/activate

# Run database migrations
flask db upgrade

# Or use Python directly
python dev.py
# Press Ctrl+C after database initializes
```

---

## 🌐 Production Deployment

### Step 1: Create Gunicorn Configuration
```bash
# As storykeep user
nano /opt/storykeep/app/gunicorn.conf.py
```

```python
# gunicorn.conf.py
import multiprocessing

bind = "127.0.0.1:8000"
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
timeout = 120
keepalive = 5

# Logging
accesslog = "/opt/storykeep/logs/access.log"
errorlog = "/opt/storykeep/logs/error.log"
loglevel = "info"

# Process naming
proc_name = "storykeep"

# Reload on code change (disable in production)
reload = False
```

### Step 2: Create Log Directory
```bash
sudo mkdir -p /opt/storykeep/logs
sudo chown storykeep:storykeep /opt/storykeep/logs
```

### Step 3: Create Supervisor Configuration
```bash
# As root
sudo nano /etc/supervisor/conf.d/storykeep.conf
```

```ini
[program:storykeep]
command=/opt/storykeep/app/venv/bin/gunicorn wsgi:app --config /opt/storykeep/app/gunicorn.conf.py
directory=/opt/storykeep/app
user=storykeep
autostart=true
autorestart=true
stopasgroup=true
killasgroup=true
stderr_logfile=/opt/storykeep/logs/supervisor_err.log
stdout_logfile=/opt/storykeep/logs/supervisor_out.log
environment=PATH="/opt/storykeep/app/venv/bin"
```

### Step 4: Start Application with Supervisor
```bash
# Update supervisor
sudo supervisorctl reread
sudo supervisorctl update

# Start application
sudo supervisorctl start storykeep

# Check status
sudo supervisorctl status storykeep
```

### Step 5: Configure Nginx
```bash
# As root
sudo nano /etc/nginx/sites-available/storykeep
```

```nginx
# /etc/nginx/sites-available/storykeep

upstream storykeep_app {
    server 127.0.0.1:8000 fail_timeout=0;
}

server {
    listen 80;
    server_name your-domain.com www.your-domain.com;
    
    # Redirect HTTP to HTTPS (after SSL is setup)
    # return 301 https://$server_name$request_uri;
    
    client_max_body_size 50M;
    
    location / {
        proxy_pass http://storykeep_app;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
        proxy_buffering off;
    }
    
    location /static {
        alias /opt/storykeep/app/photovault/static;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
    
    location /uploads {
        internal;
        alias /data/storykeep/uploads;
    }
}
```

### Step 6: Enable Nginx Site
```bash
# Create symbolic link
sudo ln -s /etc/nginx/sites-available/storykeep /etc/nginx/sites-enabled/

# Test configuration
sudo nginx -t

# Restart Nginx
sudo systemctl restart nginx
```

### Step 7: Setup SSL with Let's Encrypt
```bash
# Install Certbot
sudo apt install -y certbot python3-certbot-nginx

# Get SSL certificate
sudo certbot --nginx -d your-domain.com -d www.your-domain.com

# Certbot will automatically update Nginx config
# Test auto-renewal
sudo certbot renew --dry-run
```

---

## 🔒 Security Hardening

### Step 1: Configure Firewall (UFW)
```bash
# Enable firewall
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'
sudo ufw enable
sudo ufw status
```

### Step 2: Install Fail2ban
```bash
# Install
sudo apt install -y fail2ban

# Configure
sudo nano /etc/fail2ban/jail.local
```

```ini
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 5

[sshd]
enabled = true

[nginx-http-auth]
enabled = true

[nginx-limit-req]
enabled = true
```

```bash
# Start fail2ban
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

### Step 3: Secure PostgreSQL
```bash
# Edit postgresql.conf
sudo nano /etc/postgresql/14/main/postgresql.conf

# Set listen_addresses to local only
listen_addresses = 'localhost'

# Restart
sudo systemctl restart postgresql
```

### Step 4: Regular Updates
```bash
# Enable automatic security updates
sudo apt install -y unattended-upgrades
sudo dpkg-reconfigure -plow unattended-upgrades
```

---

## 🔧 Maintenance

### Backup Database
```bash
# Create backup script
sudo nano /opt/storykeep/backup.sh
```

```bash
#!/bin/bash
BACKUP_DIR="/opt/storykeep/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR

# Database backup
sudo -u postgres pg_dump storykeep_db | gzip > $BACKUP_DIR/db_$TIMESTAMP.sql.gz

# Uploads backup
tar -czf $BACKUP_DIR/uploads_$TIMESTAMP.tar.gz /data/storykeep/uploads

# Keep last 7 days only
find $BACKUP_DIR -name "*.gz" -mtime +7 -delete

echo "Backup completed: $TIMESTAMP"
```

```bash
# Make executable
chmod +x /opt/storykeep/backup.sh

# Add to crontab (daily at 2 AM)
sudo crontab -e
# Add line:
0 2 * * * /opt/storykeep/backup.sh
```

### Monitor Application
```bash
# View logs
sudo supervisorctl tail -f storykeep stdout
sudo supervisorctl tail -f storykeep stderr

# Restart application
sudo supervisorctl restart storykeep

# Check Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### Update Application
```bash
# As storykeep user
cd /opt/storykeep/app
git pull origin main

# Activate venv and install dependencies
source venv/bin/activate
pip install -r requirements.txt --upgrade

# Run migrations
flask db upgrade

# Restart application
sudo supervisorctl restart storykeep
```

---

## 📊 System Monitoring (Optional)

### Install Monitoring Tools
```bash
# Install htop and iotop
sudo apt install -y htop iotop

# Monitor resources
htop

# Monitor disk I/O
sudo iotop
```

---

## 🆘 Troubleshooting

### Check Application Status
```bash
sudo supervisorctl status storykeep
```

### Check Application Logs
```bash
sudo tail -f /opt/storykeep/logs/error.log
sudo tail -f /opt/storykeep/logs/supervisor_err.log
```

### Check Database Connection
```bash
sudo -u storykeep psql -U storykeep_user -d storykeep_db -h localhost
```

### Restart Everything
```bash
sudo supervisorctl restart storykeep
sudo systemctl restart nginx
sudo systemctl restart postgresql
```

---

## 📝 Quick Reference Commands

```bash
# Start/Stop/Restart
sudo supervisorctl start storykeep
sudo supervisorctl stop storykeep
sudo supervisorctl restart storykeep

# View Logs
sudo supervisorctl tail -f storykeep stdout
sudo tail -f /opt/storykeep/logs/error.log

# Update App
cd /opt/storykeep/app
git pull
source venv/bin/activate
pip install -r requirements.txt --upgrade
flask db upgrade
sudo supervisorctl restart storykeep

# Backup
/opt/storykeep/backup.sh

# Check Status
sudo supervisorctl status
sudo systemctl status nginx
sudo systemctl status postgresql
```

---

## 🎯 Summary Checklist

- [ ] Server provisioned with Ubuntu 22.04+
- [ ] Python 3.11+ installed
- [ ] PostgreSQL database created
- [ ] Application user created
- [ ] Code cloned and dependencies installed
- [ ] Environment variables configured
- [ ] Database initialized
- [ ] Gunicorn configured
- [ ] Supervisor configured
- [ ] Nginx configured
- [ ] SSL certificate installed
- [ ] Firewall enabled
- [ ] Fail2ban installed
- [ ] Backup script configured
- [ ] Application tested and running

---

## 📞 Support

For issues or questions:
- Check logs: `/opt/storykeep/logs/`
- Review this guide
- Check Flask/Gunicorn/Nginx documentation

**Congratulations!** 🎉 Your StoryKeep instance is now running on your own server.
