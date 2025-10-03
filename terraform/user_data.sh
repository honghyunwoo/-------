#!/bin/bash
# EC2 Instance Initialization Script for Owl Studio

set -e

# Update system
apt-get update
apt-get upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
usermod -aG docker ubuntu

# Install Docker Compose
curl -L "https://github.com/docker/compose/releases/download/v2.23.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Install Git
apt-get install -y git

# Install AWS CLI
apt-get install -y awscli

# Create application directory
mkdir -p /opt/owl-studio
cd /opt/owl-studio

# Clone repository (replace with your actual repository)
# git clone https://github.com/your-org/owl-studio.git .

# Create .env file with production settings
cat > .env << EOF
# Production Environment
APP_ENV=production
USE_SQLITE=false

# Database
DATABASE_URL=postgresql://owl_user:${db_password}@${db_host}:5432/owl_studio

# Redis
REDIS_HOST=${redis_host}
REDIS_PORT=6379

# S3
AWS_S3_BUCKET=${s3_bucket}
AWS_REGION=ap-northeast-2

# Add other environment variables from secrets
EOF

# Set proper permissions
chown -R ubuntu:ubuntu /opt/owl-studio

# Start services with Docker Compose
# docker-compose up -d

# Enable Docker to start on boot
systemctl enable docker

# Setup log rotation
cat > /etc/logrotate.d/owl-studio << EOF
/opt/owl-studio/logs/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 0640 ubuntu ubuntu
}
EOF

echo "Owl Studio EC2 initialization completed!"
