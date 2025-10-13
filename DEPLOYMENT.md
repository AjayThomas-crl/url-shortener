# URL Shortener - Docker Deployment Guide

## Prerequisites
- Docker installed on your machine
- Docker Compose installed
- AWS CLI configured (for AWS deployment)

## Local Development with Docker

1. **Build and run locally:**
   ```bash
   docker-compose up --build
   ```

2. **Access the application:**
   - URL Shortener: http://localhost:8000
   - Admin Dashboard: http://localhost:8000/admin
   - Health Check: http://localhost:8000/health

3. **Database:**
   - PostgreSQL runs on localhost:5432
   - Database: url_shortener
   - Username: postgres
   - Password: password

## AWS Deployment Options

### Option 1: AWS App Runner (Easiest)

1. **Create RDS PostgreSQL instance:**
   - Engine: PostgreSQL 15
   - Instance: db.t3.micro (free tier)
   - Storage: 20GB

2. **Push to GitHub and deploy:**
   - Push your code to GitHub
   - Go to AWS App Runner console
   - Create new service from source code
   - Select your repository
   - Set environment variable: `DATABASE_URL=postgresql://user:pass@rds-endpoint:5432/dbname`

### Option 2: AWS ECS with ECR

1. **Create ECR repository:**
   ```bash
   aws ecr create-repository --repository-name url-shortener
   ```

2. **Build and push Docker image:**
   ```bash
   aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com
   docker build -t url-shortener .
   docker tag url-shortener:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/url-shortener:latest
   docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/url-shortener:latest
   ```

3. **Create ECS task definition and service**

### Option 3: EC2 with Docker

1. **Launch t2.micro EC2 instance**
2. **Install Docker:**
   ```bash
   sudo yum update -y
   sudo yum install docker -y
   sudo service docker start
   sudo usermod -a -G docker ec2-user
   ```
3. **Clone and run:**
   ```bash
   git clone <your-repo>
   cd url-shortener
   docker build -t url-shortener .
   docker run -p 80:8000 -e DATABASE_URL=<your-db-url> url-shortener
   ```

## Environment Variables

Set these environment variables in production:

- `DATABASE_URL`: PostgreSQL connection string
- `PORT`: Application port (default: 8000)

## Free Tier Costs

- **EC2 t2.micro**: 750 hours/month free
- **RDS db.t3.micro**: 750 hours/month free
- **Data transfer**: 1GB/month free

## Health Check

The application includes a health check endpoint at `/health` for monitoring and load balancer health checks.