# AWS EC2 + Docker Deployment Guide

## Architecture Overview
```
Internet → EC2 (Nginx + Docker) → RDS PostgreSQL
         ↳ Docker Compose (Web App + Reverse Proxy)
```

## Step 1: Launch EC2 Instance

### 1.1 EC2 Configuration (Free Tier)
- **Instance Type**: t2.micro (1 vCPU, 1 GB RAM)
- **AMI**: Amazon Linux 2 or Ubuntu 20.04 LTS
- **Storage**: 8 GB GP2 (free tier)
- **Key Pair**: Create/use existing for SSH access

### 1.2 Security Group Rules
```bash
# HTTP Traffic
Port 80 (HTTP) - Source: 0.0.0.0/0
Port 443 (HTTPS) - Source: 0.0.0.0/0

# SSH Access
Port 22 (SSH) - Source: Your IP or 0.0.0.0/0 (less secure)

# Application Port (if direct access needed)
Port 8000 - Source: 0.0.0.0/0 (optional)
```

## Step 2: Set Up EC2 Instance

### 2.1 Connect to EC2
```bash
ssh -i your-key.pem ec2-user@your-ec2-public-ip
```

### 2.2 Install Docker & Docker Compose
```bash
# Update system
sudo yum update -y

# Install Docker
sudo yum install -y docker
sudo service docker start
sudo usermod -a -G docker ec2-user

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/1.29.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Enable Docker to start on boot
sudo systemctl enable docker

# Re-login to apply group changes
exit
ssh -i your-key.pem ec2-user@your-ec2-public-ip
```

### 2.3 Install Git and Clone Repository
```bash
sudo yum install -y git
git clone https://github.com/YourUsername/url-shortener.git
cd url-shortener
```

## Step 3: Create RDS PostgreSQL

### 3.1 Create RDS Instance (Free Tier)
```bash
aws rds create-db-instance \
    --db-instance-identifier url-shortener-db \
    --db-instance-class db.t3.micro \
    --engine postgres \
    --engine-version 15.7 \
    --allocated-storage 20 \
    --storage-type gp2 \
    --db-name url_shortener \
    --master-username dbadmin \
    --master-user-password YOUR_SECURE_PASSWORD \
    --backup-retention-period 7 \
    --port 5432 \
    --no-multi-az \
    --storage-encrypted
```

### 3.2 Configure RDS Security Group
- Inbound: PostgreSQL (5432) from EC2 Security Group
- Outbound: All traffic

## Step 4: Deploy Application

### 4.1 Create Production Environment File
```bash
# Create .env.production on EC2
DATABASE_URL=postgresql://dbadmin:password@your-rds-endpoint.amazonaws.com:5432/url_shortener
PORT=8000
PYTHONPATH=/app
```

### 4.2 Run Docker Compose
```bash
# Build and start services
docker-compose -f docker-compose.prod.yml up -d --build

# Check logs
docker-compose -f docker-compose.prod.yml logs -f
```

## Step 5: Set Up Nginx Reverse Proxy

### 5.1 Install Nginx
```bash
sudo yum install -y nginx
sudo systemctl start nginx
sudo systemctl enable nginx
```

### 5.2 Configure Nginx
```bash
sudo nano /etc/nginx/nginx.conf
```

## Step 6: SSL Certificate (Let's Encrypt)

### 6.1 Install Certbot
```bash
sudo yum install -y certbot python3-certbot-nginx
```

### 6.2 Obtain SSL Certificate
```bash
sudo certbot --nginx -d yourdomain.com
```

## Cost Estimation (Monthly)
- **EC2 t2.micro**: Free (first 12 months)
- **RDS t3.micro**: ~$13-15/month (after free tier)
- **EBS Storage**: Free (30 GB)
- **Data Transfer**: Minimal for low traffic
- **Total**: ~$15-20/month after free tier

## Monitoring & Maintenance
- CloudWatch monitoring
- Automatic backups via RDS
- Docker container health checks
- Log rotation setup