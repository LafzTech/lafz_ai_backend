# Installation Guide

## Quick Start (Recommended)

### 1. Setup Environment

```bash
# Clone the repository
git clone <your-repo>
cd lafz_ai

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Run automated setup
python setup.py
```

### 2. Configure Environment

```bash
# Copy and edit environment file
cp .env.example .env
# Edit .env with your API keys
```

### 3. Start Services

```bash
# Start Redis
docker run -d --name redis -p 6379:6379 redis:7-alpine

# Start the application
python run.py dev
```

## Manual Installation (If automated setup fails)

### Prerequisites

- Python 3.11+
- Redis (via Docker or local installation)
- FFmpeg (for audio processing)

### Step-by-Step Installation

#### 1. System Dependencies

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install -y python3-pip python3-venv ffmpeg libsndfile1
```

**macOS:**
```bash
brew install python ffmpeg libsndfile
```

**Windows:**
- Install Python 3.11+ from python.org
- Install FFmpeg from https://ffmpeg.org/
- Or use chocolatey: `choco install python ffmpeg`

#### 2. Python Environment

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install core dependencies
pip install -r requirements.txt
```

#### 3. Environment Configuration

```bash
cp .env.example .env
```

Edit `.env` with your API keys:

```bash
# Required API Keys
OPENAI_API_KEY=sk-your-openai-key
GOOGLE_MAPS_API_KEY=your-google-maps-key
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json

# AWS Configuration
AWS_ACCESS_KEY_ID=your-aws-key
AWS_SECRET_ACCESS_KEY=your-aws-secret
AWS_BEDROCK_AGENT_ID=your-agent-id

# Ride API
RIDE_API_BASE_URL=http://192.168.1.2:8000
```

#### 4. Start Redis

**Using Docker (Recommended):**
```bash
docker run -d --name redis -p 6379:6379 redis:7-alpine
```

**Local Installation:**
```bash
# Ubuntu/Debian
sudo apt-get install redis-server
sudo systemctl start redis

# macOS
brew install redis
brew services start redis
```

#### 5. Run Application

```bash
# Development mode
python main.py

# Or using the runner script
python run.py dev
```

## Troubleshooting

### Common Issues

#### 1. Module Import Errors

If you get import errors, ensure you're in the virtual environment:

```bash
source .venv/bin/activate
pip list  # Check installed packages
```

#### 2. Audio Processing Issues

If audio features don't work:

```bash
# Install system audio libraries
sudo apt-get install ffmpeg libsndfile1

# Install optional audio packages
pip install soundfile librosa
```

#### 3. Redis Connection Issues

```bash
# Check if Redis is running
redis-cli ping

# If using Docker
docker ps | grep redis
docker logs redis
```

#### 4. Google Cloud Authentication

```bash
# Set environment variable
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account.json"

# Or add to .env file
echo 'GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account.json"' >> .env
```

#### 5. AWS Bedrock Access

Ensure your AWS credentials have Bedrock permissions:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "bedrock:*"
            ],
            "Resource": "*"
        }
    ]
}
```

### Minimal Installation (Core Features Only)

If you're having dependency issues, you can run with minimal features:

```bash
# Install only core dependencies
pip install fastapi uvicorn redis requests openai google-cloud-translate google-cloud-texttospeech googlemaps boto3 pydantic python-dotenv

# Skip audio processing features
# Set in .env: ENABLE_VOICE_FEATURES=false
```

## Docker Installation (Alternative)

If local installation fails, use Docker:

```bash
# Build and run with Docker Compose
docker-compose up -d

# Access the application at http://localhost:8000
```

## Development Setup

For development with all features:

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Setup pre-commit hooks
pre-commit install

# Run tests
pytest

# Format code
black app/ main.py
isort app/ main.py
```

## Production Deployment

```bash
# Using Docker Compose
docker-compose -f deployment/docker-compose.prod.yml up -d

# Manual deployment
pip install -r requirements.txt
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker
```

## API Key Setup Guide

### OpenAI API Key
1. Visit https://platform.openai.com/api-keys
2. Create a new API key
3. Add to `.env`: `OPENAI_API_KEY=sk-...`

### Google Cloud Setup
1. Create a project at https://console.cloud.google.com/
2. Enable APIs: Translation, Text-to-Speech, Places
3. Create a service account and download JSON key
4. Set `GOOGLE_APPLICATION_CREDENTIALS` path

### AWS Bedrock Setup
1. Ensure Bedrock access in your AWS region
2. Create IAM user with Bedrock permissions
3. Set AWS credentials in `.env`
4. Create Bedrock Agent (see main README)

## Support

If you continue having issues:

1. Check the logs: `tail -f logs/app.log`
2. Verify environment: `python -c "import sys; print(sys.version)"`
3. Test API keys: `python -c "import openai; print('OK')"`
4. Create an issue with error details

## Minimum Working Example

For testing basic functionality:

```python
# test_basic.py
import requests

response = requests.post("http://localhost:8000/api/chat", json={
    "message": "Hello",
    "language": "en"
})

print(response.json())
```