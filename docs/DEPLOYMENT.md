# Deployment Guide

This document outlines the steps to deploy the LinkedIn Lead Generation system to an Azure VM.

## Prerequisites

- Azure VM with Ubuntu Server 20.04 LTS or higher
- Docker and Docker Compose installed
- Domain name (optional for production)
- SSL certificates (optional for production)

## Deployment Steps

### 1. Set Up Azure VM

1. Create an Azure VM with Ubuntu Server
2. Open ports 80 and 443 for HTTP/HTTPS traffic
3. Set up a static IP address
4. (Optional) Associate a domain name with the VM

### 2. Install Docker and Docker Compose

```bash
# Update package index
sudo apt update

# Install dependencies
sudo apt install -y apt-transport-https ca-certificates curl software-properties-common

# Add Docker's official GPG key
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -

# Add Docker repository
sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"

# Install Docker
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io

# Add current user to docker group
sudo usermod -aG docker ${USER}
sudo chmod 666 /var/run/docker.sock

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.12.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### 3. Clone Repository

```bash
# Clone the repository
git clone https://github.com/yourusername/linkedin-lead-gen.git
cd linkedin-lead-gen
```

### 4. Set Up Environment Variables

Create a `.env` file with the required environment variables:

```bash
# Copy the example env file
cp .env.example .env

# Edit the env file with your values
nano .env
```

Update the following values:

- `API_KEY`: A secure API key for authentication
- `SUPABASE_URL`: Your Supabase URL
- `SUPABASE_ANON_KEY`: Your Supabase anonymous key
- `SUPABASE_SERVICE_ROLE_KEY`: Your Supabase service role key
- `OPENAI_API_KEY`: Your OpenAI API key
- `SERPAPI_API_KEY`: Your SerpAPI key
- `PROXYCURL_API_KEY`: Your ProxyCurl API key
- `GOOGLE_API_CREDENTIALS`: Path to your Google API credentials JSON file
- `GOOGLE_SHEET_ID`: Your Google Sheet ID

### 5. Set Up SSL Certificates (Production)

For production deployment, set up SSL certificates:

```bash
# Create certificates directory
mkdir -p nginx/certs

# Using Let's Encrypt (recommended for production)
sudo apt install -y certbot
sudo certbot certonly --standalone -d yourdomain.com

# Copy certificates
sudo cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem nginx/certs/server.crt
sudo cp /etc/letsencrypt/live/yourdomain.com/privkey.pem nginx/certs/server.key
```

For development or testing, you can create self-signed certificates:

```bash
# Create self-signed certificates (for development only)
openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout nginx/certs/server.key -out nginx/certs/server.crt
```

### 6. Deploy the Application

```bash
# Start the application
docker-compose up -d

# Check the logs
docker-compose logs -f
```

### 7. Verify Deployment

```bash
# Check if the application is running
curl http://localhost/api/health
```

You should receive a response with the status "healthy".

### 8. Set Up Monitoring (Optional)

For production deployments, it's recommended to set up monitoring:

```bash
# Install Node Exporter for Prometheus
docker run -d \
  --name=node-exporter \
  --restart=always \
  --net="host" \
  --pid="host" \
  -v "/:/host:ro,rslave" \
  quay.io/prometheus/node-exporter:latest \
  --path.rootfs=/host
```

### 9. Set Up Automatic Updates (Optional)

To ensure the application stays up-to-date:

```bash
# Create update script
cat > update.sh << 'EOF'
#!/bin/bash
cd /path/to/linkedin-lead-gen
git pull
docker-compose up -d --build
EOF

# Make it executable
chmod +x update.sh

# Add to crontab to run weekly
(crontab -l 2>/dev/null; echo "0 0 * * 0 /path/to/update.sh") | crontab -
```

## Troubleshooting

### Application not accessible

1. Check if containers are running: `docker-compose ps`
2. Check container logs: `docker-compose logs -f`
3. Verify firewall settings: `sudo ufw status`
4. Check Nginx configuration: `docker-compose exec nginx nginx -t`

### Database connection issues

1. Verify Supabase credentials in `.env`
2. Check network connectivity to Supabase

### API errors

1. Check API logs: `docker-compose logs -f api`
2. Verify API keys in `.env`

## Maintenance

### Updating the Application

```bash
# Pull latest changes
git pull

# Rebuild and restart containers
docker-compose up -d --build
```

### Backing Up Data

The application uses Supabase as the database, which handles backups automatically. For additional backup:

```bash
# Export database
pg_dump -h your_supabase_db_host -U postgres -d postgres > backup.sql
```

### Scaling

For higher load, consider:

1. Increasing VM resources
2. Implementing load balancing with multiple VMs
3. Utilizing Azure's autoscaling features
