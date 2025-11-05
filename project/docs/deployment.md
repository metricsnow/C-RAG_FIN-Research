# Deployment Guide

This document provides comprehensive instructions for deploying the Financial Research Assistant application.

## Overview

The application consists of:
- **Streamlit Frontend**: Web interface (port 8501)
- **Ollama LLM Service**: Local LLM server (port 11434)
- **ChromaDB**: Vector database (persistent storage in `data/chroma_db/`)

**Important**: Ollama requires self-hosting, so Streamlit Cloud is not an option. You must deploy to a VPS or use local deployment with ngrok tunneling.

## Deployment Options

### Option 1: Local Deployment (Development/Demo)

**Use Case**: Local development, demos, testing

**Requirements**:
- Local machine with Python 3.11+
- Ollama installed and running
- Virtual environment set up

**Steps**:

1. **Activate virtual environment**:
   ```bash
   source venv/bin/activate
   ```

2. **Configure environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env and add your OPENAI_API_KEY (if using OpenAI embeddings)
   ```

3. **Verify Ollama is running**:
   ```bash
   ollama serve
   # In another terminal, verify it's working:
   curl http://localhost:11434/api/tags
   ```

4. **Run the application**:
   ```bash
   # Option 1: Using deployment script
   bash scripts/deploy_local.sh

   # Option 2: Direct command
   python scripts/run_streamlit.py

   # Option 3: Streamlit command
   streamlit run app/ui/app.py
   ```

5. **Access the application**:
   - Open browser to: `http://localhost:8501`

### Option 2: Local Deployment with ngrok (Demo/Testing)

**Use Case**: Demo to external users, testing external access

**Requirements**:
- All requirements from Option 1
- ngrok installed ([download](https://ngrok.com/download))

**Steps**:

1. **Install ngrok**:
   ```bash
   # macOS
   brew install ngrok/ngrok/ngrok

   # Or download from https://ngrok.com/download
   ```

2. **Authenticate ngrok** (first time only):
   ```bash
   ngrok config add-authtoken YOUR_AUTH_TOKEN
   # Get token from: https://dashboard.ngrok.com/get-started/your-authtoken
   ```

3. **Run deployment script**:
   ```bash
   bash scripts/deploy_with_ngrok.sh
   ```

4. **Access the application**:
   - Public URL: Shown in terminal (e.g., `https://abc123.ngrok.io`)
   - Local URL: `http://localhost:8501`
   - ngrok Dashboard: `http://localhost:4040`

**Note**: Free ngrok URLs change on each restart. For permanent URLs, use VPS deployment.

### Option 3: VPS Deployment (Production)

**Use Case**: Production deployment, permanent access

**Recommended VPS Providers**:
- DigitalOcean ($5-10/month)
- Linode ($5-10/month)
- AWS EC2 (pay-as-you-go)
- Google Cloud Platform (pay-as-you-go)

**Requirements**:
- VPS with Ubuntu 20.04+ or similar Linux distribution
- Minimum: 2GB RAM, 20GB storage (4GB RAM recommended for Ollama)
- Root/SSH access

**Steps**:

#### 1. Server Setup

```bash
# SSH into your VPS
ssh user@your-vps-ip

# Update system
sudo apt update && sudo apt upgrade -y

# Install Python 3.11+
sudo apt install python3.11 python3.11-venv python3-pip -y

# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Install system dependencies
sudo apt install build-essential curl git -y
```

#### 2. Clone and Setup Project

```bash
# Clone repository (or upload project files)
git clone YOUR_REPO_URL
cd project

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies (modern method using pyproject.toml)
pip install --upgrade pip setuptools wheel
pip install -e .

# Alternative: Legacy method using requirements.txt (still supported)
# pip install -r requirements.txt

# Configure environment
cp .env.example .env
nano .env  # Edit with your configuration
```

#### 3. Configure Ollama

```bash
# Start Ollama service
ollama serve

# In another terminal or screen session:
ollama pull llama3.2  # Or mistral

# Verify Ollama is running
curl http://localhost:11434/api/tags
```

#### 4. Configure Streamlit for Production

The `.streamlit/config.toml` file is already configured for production with:
- External access enabled (`address = "0.0.0.0"`)
- Security settings enabled
- Performance optimizations

#### 5. Set Up Process Management (systemd)

Create a systemd service for Streamlit:

```bash
sudo nano /etc/systemd/system/streamlit-app.service
```

Add the following content:

```ini
[Unit]
Description=Streamlit Financial Research Assistant
After=network.target

[Service]
Type=simple
User=your-username
WorkingDirectory=/path/to/project
Environment="PATH=/path/to/project/venv/bin"
ExecStart=/path/to/project/venv/bin/streamlit run app/ui/app.py --server.port=8501 --server.address=0.0.0.0
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start the service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable streamlit-app
sudo systemctl start streamlit-app
sudo systemctl status streamlit-app
```

#### 6. Configure Firewall

```bash
# Allow HTTP/HTTPS (if using reverse proxy)
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Allow Streamlit port (if accessing directly)
sudo ufw allow 8501/tcp

# Enable firewall
sudo ufw enable
```

#### 7. Set Up Reverse Proxy (Optional but Recommended)

Using Nginx as reverse proxy:

```bash
# Install Nginx
sudo apt install nginx -y

# Create Nginx configuration
sudo nano /etc/nginx/sites-available/streamlit-app
```

Add configuration:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;
    }
}
```

Enable and restart Nginx:

```bash
sudo ln -s /etc/nginx/sites-available/streamlit-app /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

#### 8. SSL Certificate (Optional but Recommended)

Using Let's Encrypt:

```bash
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d your-domain.com
```

#### 9. Access Application

- Direct: `http://your-vps-ip:8501`
- With domain: `http://your-domain.com` (if configured)
- With SSL: `https://your-domain.com` (if configured)

## Environment Variables

The application uses **Pydantic-based configuration** with automatic type validation. Configuration is loaded from `.env` file or system environment variables.

Key environment variables (configure in `.env`):

```bash
# Ollama Configuration
OLLAMA_BASE_URL=http://localhost:11434  # Change to server IP if Ollama on different machine
OLLAMA_TIMEOUT=30                        # Must be >= 1
OLLAMA_MAX_RETRIES=3                     # Must be >= 0
OLLAMA_TEMPERATURE=0.7                   # Range: 0.0 - 2.0
OLLAMA_PRIORITY=1                        # Must be >= 0
OLLAMA_ENABLED=true                      # true/false, 1/0, yes/no

# OpenAI (for embeddings - optional)
OPENAI_API_KEY=your_key_here

# ChromaDB
CHROMA_DB_PATH=./data/chroma_db
CHROMA_PERSIST_DIRECTORY=./data/chroma_db

# Embedding Provider
EMBEDDING_PROVIDER=openai  # or "ollama"

# LLM Configuration
LLM_PROVIDER=ollama
LLM_MODEL=llama3.2

# Logging Configuration (optional)
LOG_LEVEL=INFO                           # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FILE=./logs/app.log                  # Optional: log file path
LOG_FILE_MAX_BYTES=10485760              # 10MB (minimum 1024)
LOG_FILE_BACKUP_COUNT=5                  # Must be >= 1

# Application Configuration (optional)
MAX_DOCUMENT_SIZE_MB=10                  # Must be >= 1
DEFAULT_TOP_K=5                          # Must be >= 1
```

**Note**: All configuration values are automatically validated by Pydantic. Invalid values (e.g., `OLLAMA_TIMEOUT=0` or `LOG_LEVEL=INVALID`) will cause the application to fail at startup with clear error messages indicating what needs to be fixed.

## Service Management

### Check Service Status

```bash
# Streamlit (if using systemd)
sudo systemctl status streamlit-app

# Ollama
systemctl status ollama  # If installed as service
# Or check manually:
curl http://localhost:11434/api/tags
```

### View Logs

```bash
# Streamlit logs
sudo journalctl -u streamlit-app -f

# Or if running manually:
# Logs appear in terminal
```

### Restart Services

```bash
# Streamlit
sudo systemctl restart streamlit-app

# Ollama
sudo systemctl restart ollama
```

## Monitoring and Health Checks

### Health Check Endpoints

The application provides health check endpoints for monitoring and orchestration:

```bash
# Comprehensive health check
curl http://localhost:8080/health

# Liveness probe (application running)
curl http://localhost:8080/health/live

# Readiness probe (application ready to serve)
curl http://localhost:8080/health/ready
```

**Health Check Response** (example):
```json
{
  "status": "healthy",
  "timestamp": 1706380800.0,
  "components": {
    "chromadb": {
      "status": "healthy",
      "document_count": 150,
      "collection": "documents"
    },
    "ollama": {
      "status": "healthy",
      "base_url": "http://localhost:11434",
      "models_available": 1
    }
  }
}
```

### Prometheus Metrics

Metrics are exposed in Prometheus format for monitoring:

```bash
# View metrics
curl http://localhost:8000/metrics
```

**Available Metrics**:
- `rag_queries_total` - Total RAG queries (with status label)
- `rag_query_duration_seconds` - RAG query processing duration
- `document_ingestion_total` - Total documents ingested
- `vector_db_operations_total` - Vector database operations
- `llm_requests_total` - LLM API requests
- `system_uptime_seconds` - System uptime
- `system_health_status` - System health status (1 = healthy, 0 = unhealthy)

**Prometheus Configuration** (example `prometheus.yml`):
```yaml
scrape_configs:
  - job_name: 'financial-research-assistant'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
    scrape_interval: 15s
```

### Monitoring Best Practices

1. **Health Checks**:
   - Configure load balancers to use `/health/ready` for readiness checks
   - Use `/health/live` for liveness probes in Kubernetes
   - Monitor health check status regularly

2. **Metrics Collection**:
   - Set up Prometheus to scrape metrics endpoint
   - Configure Grafana dashboards for visualization
   - Set up alerts for error rates and system health

3. **Key Metrics to Monitor**:
   - Query duration (p95, p99)
   - Error rates (queries, ingestion, LLM requests)
   - System uptime
   - Vector database operation performance
   - Document ingestion throughput

4. **Alerting**:
   - Alert on health check failures
   - Alert on high error rates (>5% of requests)
   - Alert on slow query performance (p95 > 10s)
   - Alert on system downtime

### Disabling Monitoring

If you need to disable monitoring:

```bash
# In .env file
METRICS_ENABLED=false
HEALTH_CHECK_ENABLED=false
```

Note: Disabling monitoring is not recommended for production deployments.

## Troubleshooting

### Streamlit Not Accessible

1. **Check if Streamlit is running**:
   ```bash
   ps aux | grep streamlit
   ```

2. **Check port is not blocked**:
   ```bash
   sudo netstat -tulpn | grep 8501
   ```

3. **Check firewall**:
   ```bash
   sudo ufw status
   ```

4. **Check Streamlit config**:
   - Verify `.streamlit/config.toml` has `address = "0.0.0.0"`

### Ollama Connection Issues

1. **Verify Ollama is running**:
   ```bash
   curl http://localhost:11434/api/tags
   ```

2. **Check Ollama URL in .env**:
   - For local: `OLLAMA_BASE_URL=http://localhost:11434`
   - For remote: `OLLAMA_BASE_URL=http://ollama-server-ip:11434`

3. **Check network connectivity**:
   ```bash
   ping localhost  # For local
   # Or
   ping ollama-server-ip  # For remote
   ```

### ChromaDB Issues

1. **Check data directory permissions**:
   ```bash
   ls -la data/chroma_db
   ```

2. **Verify ChromaDB path in .env**:
   ```bash
   CHROMA_DB_PATH=./data/chroma_db
   ```

3. **Check disk space**:
   ```bash
   df -h
   ```

### Performance Issues

1. **Ollama model size**: Larger models require more RAM
   - llama3.2: ~2GB RAM
   - mistral: ~4GB RAM

2. **ChromaDB optimization**:
   - Ensure sufficient disk space
   - Consider SSD for better performance

3. **Streamlit configuration**:
   - Adjust `maxUploadSize` in `.streamlit/config.toml`
   - Monitor memory usage

## Security Considerations

1. **Environment Variables**: Never commit `.env` file
2. **API Keys**: Store securely, rotate regularly
3. **Firewall**: Only expose necessary ports
4. **SSL**: Use HTTPS in production
5. **Access Control**: Consider adding authentication for production
6. **Updates**: Keep system and dependencies updated

## Next Steps

After deployment:
- Test all functionality end-to-end
- Monitor performance and logs
- Set up backups for ChromaDB data
- Consider adding monitoring/alerting
- Document any custom configurations

## Support

For issues:
1. Check logs (see Service Management section)
2. Verify all services are running
3. Check environment variables
4. Review troubleshooting section above
