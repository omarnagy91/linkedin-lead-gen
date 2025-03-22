# LinkedIn Lead Generation - Deployment Guide

This guide provides instructions for setting up and deploying the LinkedIn Lead Generation system. Follow these steps to get the application running with Docker.

## Prerequisites

- Docker and Docker Compose installed
- Git (to clone the repository)
- OpenSSL (if generating SSL certificates)

## Quick Start

1. Clone the repository
   ```bash
   git clone <repository-url>
   cd linkedin-lead-gen
   ```

2. Create `.env` file with your environment variables (copy from `.env.example`)
   ```bash
   cp .env.example .env
   # Edit .env with your values
   ```

3. Build and start the containers
   ```bash
   docker-compose up -d
   ```

4. Verify the application is running
   ```bash
   # Check the API health endpoint
   curl http://localhost/health
   
   # Or open in browser: http://localhost/health
   ```

## Configuration

### Environment Variables

The application uses environment variables for configuration. Create a `.env` file in the project root with the following variables:

```
# API Configuration
API_PREFIX=/api
DEBUG=true

# Database Configuration
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_supabase_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key

# External APIs
PROXYCURL_API_KEY=your_proxycurl_api_key
OPENAI_API_KEY=your_openai_api_key

# Google Sheets 
GOOGLE_SHEET_ID=your_google_sheet_id
```

### Troubleshooting

If you encounter issues with the deployment, check the following:

1. **Email validation errors**: The application requires the `email-validator` package. It's included in the requirements.txt, but if you're getting errors, you can install it manually:

   ```bash
   docker exec -it linkedin-lead-gen-api-1 pip install email-validator
   ```

2. **Nginx SSL certificate errors**: For development, the system is configured to run with HTTP only. If you need HTTPS:

   ```bash
   # Generate self-signed certificates
   cd scripts
   ./generate_certs.sh  # Linux/macOS
   # or
   powershell -ExecutionPolicy Bypass -File .\generate_certs.ps1  # Windows
   
   # Then edit nginx/default.conf to uncomment the HTTPS server block
   ```

3. **API not reachable via Nginx**: If you can't access the API through Nginx, check:
   - Ensure both containers are running: `docker-compose ps`
   - Check Nginx logs: `docker-compose logs nginx`
   - Check API logs: `docker-compose logs api`
   - Verify the API health directly: `curl http://localhost:8000/api/health`

## Production Deployment

For production deployment, additional steps are recommended:

1. Enable HTTPS by generating proper SSL certificates (Let's Encrypt recommended)
2. Update the Nginx configuration to use SSL
3. Set `DEBUG=false` in the .env file
4. Configure proper database backup procedures
5. Set up monitoring and logging solutions

## SSL Configuration

To enable HTTPS for production:

1. Obtain proper SSL certificates (Let's Encrypt recommended)
2. Place the certificates in `nginx/certs/`:
   - Certificate: `nginx/certs/server.crt`
   - Private key: `nginx/certs/server.key`

3. Edit `nginx/default.conf` to uncomment the HTTPS server block and comment out the HTTP-only configuration.

4. Restart the containers:
   ```bash
   docker-compose down
   docker-compose up -d
   ```

## Updating the Application

To update the application:

1. Pull the latest changes:
   ```bash
   git pull origin main
   ```

2. Rebuild and restart containers:
   ```bash
   docker-compose down
   docker-compose build
   docker-compose up -d
   ```

## Backup and Restore

The application data is stored in the configured Supabase database. Refer to Supabase documentation for backup procedures.
