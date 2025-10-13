#!/bin/bash

# EC2 Deployment Script for URL Shortener
# Run this script on your EC2 instance after cloning the repository

set -e

echo "🚀 Starting URL Shortener deployment on EC2..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   print_error "This script should not be run as root"
   exit 1
fi

# Detect OS and update system packages
print_status "Updating system packages..."
if command -v apt &> /dev/null; then
    # Ubuntu/Debian
    sudo apt update -y
    PACKAGE_MANAGER="apt"
elif command -v yum &> /dev/null; then
    # Amazon Linux/CentOS
    sudo yum update -y
    PACKAGE_MANAGER="yum"
else
    print_error "Unsupported operating system"
    exit 1
fi

# Install Docker if not present
if ! command -v docker &> /dev/null; then
    print_status "Installing Docker..."
    if [ "$PACKAGE_MANAGER" = "apt" ]; then
        # Ubuntu/Debian Docker installation
        sudo apt install -y apt-transport-https ca-certificates curl software-properties-common
        curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
        sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"
        sudo apt update
        sudo apt install -y docker-ce
    else
        # Amazon Linux/CentOS
        sudo yum install -y docker
    fi
    sudo service docker start
    sudo usermod -a -G docker $USER
    sudo systemctl enable docker
    print_warning "Please logout and login again to apply Docker group changes"
else
    print_status "Docker is already installed"
fi

# Install Docker Compose if not present
if ! command -v docker-compose &> /dev/null; then
    print_status "Installing Docker Compose..."
    sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
else
    print_status "Docker Compose is already installed"
fi

# Install Nginx
if ! command -v nginx &> /dev/null; then
    print_status "Installing Nginx..."
    if [ "$PACKAGE_MANAGER" = "apt" ]; then
        sudo apt install -y nginx
    else
        sudo yum install -y nginx
    fi
    sudo systemctl enable nginx
else
    print_status "Nginx is already installed"
fi

# Create SSL directory
print_status "Creating SSL directory..."
sudo mkdir -p /etc/nginx/ssl
sudo mkdir -p ./ssl

# Check if .env.production exists
if [ ! -f ".env.production" ]; then
    print_warning "Creating .env.production template..."
    cat > .env.production << EOF
# Replace these values with your actual RDS endpoint and credentials
DATABASE_URL=postgresql://dbadmin:your_password@your-rds-endpoint.amazonaws.com:5432/url_shortener
PORT=8000
PYTHONPATH=/app
EOF
    print_error "Please edit .env.production with your actual database credentials"
    exit 1
fi

# Build and start services
print_status "Building and starting Docker services..."
docker-compose -f docker-compose.prod.yml down 2>/dev/null || true
docker-compose -f docker-compose.prod.yml up -d --build

# Wait for services to be ready
print_status "Waiting for services to be ready..."
sleep 30

# Check service status
if docker-compose -f docker-compose.prod.yml ps | grep -q "Up"; then
    print_status "Services are running successfully!"
    docker-compose -f docker-compose.prod.yml ps
else
    print_error "Some services failed to start"
    docker-compose -f docker-compose.prod.yml logs
    exit 1
fi

# Install and configure Certbot for SSL (if domain is configured)
read -p "Do you have a domain name configured? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    read -p "Enter your domain name: " domain_name
    
    print_status "Installing Certbot..."
    sudo yum install -y certbot python3-certbot-nginx
    
    print_status "Obtaining SSL certificate..."
    sudo certbot --nginx -d $domain_name --non-interactive --agree-tos --email admin@$domain_name
    
    # Update nginx config with domain
    sed -i "s/your-domain.com/$domain_name/g" nginx.conf
    
    # Restart nginx
    sudo systemctl restart nginx
fi

# Display final status
print_status "Deployment completed successfully! 🎉"
echo
echo "📋 Service Status:"
docker-compose -f docker-compose.prod.yml ps
echo
echo "🌐 Access your application:"
if [[ $domain_name ]]; then
    echo "   HTTPS: https://$domain_name"
    echo "   HTTP:  http://$domain_name (redirects to HTTPS)"
else
    EXTERNAL_IP=$(curl -s http://checkip.amazonaws.com)
    echo "   HTTP:  http://$EXTERNAL_IP"
    echo "   Direct: http://$EXTERNAL_IP:8000"
fi
echo
echo "📊 View logs: docker-compose -f docker-compose.prod.yml logs -f"
echo "🔄 Restart: docker-compose -f docker-compose.prod.yml restart"
echo "⛔ Stop: docker-compose -f docker-compose.prod.yml down"