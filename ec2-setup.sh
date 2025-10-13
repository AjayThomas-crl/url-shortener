#!/bin/bash

# Quick EC2 Setup Commands
# Copy and paste these commands one by one on your EC2 instance

# 1. Update system and install dependencies
sudo yum update -y
sudo yum install -y git docker nginx

# 2. Start and enable Docker
sudo service docker start
sudo systemctl enable docker
sudo usermod -a -G docker ec2-user

# 3. Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 4. Clone your repository (replace with your GitHub repo)
git clone https://github.com/YourUsername/url-shortener.git
cd url-shortener

# 5. Create environment file
cat > .env.production << 'EOF'
DATABASE_URL=postgresql://dbadmin:your_password@your-rds-endpoint.amazonaws.com:5432/url_shortener
PORT=8000
PYTHONPATH=/app
EOF

# 6. Make deploy script executable
chmod +x deploy-ec2.sh

# 7. Run deployment (after editing .env.production)
# ./deploy-ec2.sh

echo "Setup completed! Next steps:"
echo "1. Edit .env.production with your RDS credentials"
echo "2. Run: ./deploy-ec2.sh"